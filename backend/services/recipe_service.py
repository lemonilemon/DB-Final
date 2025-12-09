from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.recipe import Recipe, RecipeRequirement, RecipeStep, RecipeReview, MealPlan
from models.inventory import Ingredient
from models.user import User
from schemas.recipe import (
    RecipeCreateRequest,
    RecipeBasicResponse,
    RecipeDetailResponse,
    RecipeRequirementResponse,
    RecipeStepResponse,
    CookRecipeRequest,
    CookRecipeResponse,
    ReviewCreateRequest,
    ReviewResponse,
    MealPlanCreateRequest,
    MealPlanResponse,
)
from services.inventory_service import InventoryService
from services.fridge_service import FridgeService
from services.behavior_service import BehaviorService


class RecipeService:
    """Service for recipe management and cooking."""

    # ========================================================================
    # Recipe Management
    # ========================================================================

    @staticmethod
    async def create_recipe(
        request: RecipeCreateRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> Recipe:
        """
        Create a new recipe with requirements and steps.
        """
        # Create recipe
        new_recipe = Recipe(
            owner_id=current_user_id,
            recipe_name=request.recipe_name,
            description=request.description,
            cooking_time=request.cooking_time,
            status="Published"
        )
        session.add(new_recipe)
        await session.flush()  # Get recipe_id

        # Add requirements
        for req in request.requirements:
            # Verify ingredient exists
            ingredient = await InventoryService.get_ingredient(req.ingredient_id, session)

            requirement = RecipeRequirement(
                recipe_id=new_recipe.recipe_id,
                ingredient_id=req.ingredient_id,
                quantity_needed=req.quantity_needed
            )
            session.add(requirement)

        # Add steps
        for step in request.steps:
            recipe_step = RecipeStep(
                recipe_id=new_recipe.recipe_id,
                step_number=step.step_number,
                description=step.description
            )
            session.add(recipe_step)

        await session.commit()
        await session.refresh(new_recipe)
        return new_recipe

    @staticmethod
    async def get_all_recipes(
        session: AsyncSession,
        search: str = None
    ) -> List[RecipeBasicResponse]:
        """Get all recipes with average ratings."""
        query = select(Recipe, User).join(User, Recipe.owner_id == User.user_id)

        if search:
            query = query.where(Recipe.recipe_name.ilike(f"%{search}%"))

        query = query.order_by(Recipe.created_at.desc())

        result = await session.execute(query)
        rows = result.all()

        recipes = []
        for recipe, user in rows:
            # Get average rating and review count
            rating_result = await session.execute(
                select(
                    func.avg(RecipeReview.rating),
                    func.count(RecipeReview.rating)
                ).where(RecipeReview.recipe_id == recipe.recipe_id)
            )
            avg_rating, review_count = rating_result.one()

            recipes.append(
                RecipeBasicResponse(
                    recipe_id=recipe.recipe_id,
                    owner_id=recipe.owner_id,
                    owner_name=user.user_name,
                    recipe_name=recipe.recipe_name,
                    description=recipe.description,
                    cooking_time=recipe.cooking_time,
                    status=recipe.status,
                    created_at=recipe.created_at,
                    updated_at=recipe.updated_at,
                    avg_rating=float(avg_rating) if avg_rating else None,
                    total_reviews=review_count
                )
            )

        return recipes

    @staticmethod
    async def get_recipe_detail(
        recipe_id: int,
        session: AsyncSession,
        current_user_id: Optional[UUID] = None
    ) -> RecipeDetailResponse:
        """Get detailed recipe with requirements and steps."""
        # Get recipe with owner
        result = await session.execute(
            select(Recipe, User)
            .join(User, Recipe.owner_id == User.user_id)
            .where(Recipe.recipe_id == recipe_id)
        )
        row = result.one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="Recipe not found")

        recipe, user = row

        # Get requirements with ingredient details
        req_result = await session.execute(
            select(RecipeRequirement, Ingredient)
            .join(Ingredient, RecipeRequirement.ingredient_id == Ingredient.ingredient_id)
            .where(RecipeRequirement.recipe_id == recipe_id)
            .order_by(Ingredient.name)
        )
        req_rows = req_result.all()

        requirements = []
        for req, ingredient in req_rows:
            requirements.append(
                RecipeRequirementResponse(
                    ingredient_id=ingredient.ingredient_id,
                    ingredient_name=ingredient.name,
                    standard_unit=ingredient.standard_unit,
                    quantity_needed=req.quantity_needed
                )
            )

        # Get steps
        steps_result = await session.execute(
            select(RecipeStep)
            .where(RecipeStep.recipe_id == recipe_id)
            .order_by(RecipeStep.step_number)
        )
        steps = steps_result.scalars().all()

        step_responses = [
            RecipeStepResponse(
                step_number=step.step_number,
                description=step.description
            )
            for step in steps
        ]

        # Get ratings
        rating_result = await session.execute(
            select(
                func.avg(RecipeReview.rating),
                func.count(RecipeReview.rating)
            ).where(RecipeReview.recipe_id == recipe_id)
        )
        avg_rating, review_count = rating_result.one()

        # Log view action
        if current_user_id:
            await BehaviorService.log_user_action(
                action_type="view_recipe",
                user_id=current_user_id,
                resource_type="recipe",
                resource_id=str(recipe_id),
                metadata={
                    "recipe_name": recipe.recipe_name,
                    "cooking_time": recipe.cooking_time
                }
            )

        return RecipeDetailResponse(
            recipe_id=recipe.recipe_id,
            owner_id=recipe.owner_id,
            owner_name=user.user_name,
            recipe_name=recipe.recipe_name,
            description=recipe.description,
            cooking_time=recipe.cooking_time,
            status=recipe.status,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at,
            requirements=requirements,
            steps=step_responses,
            avg_rating=float(avg_rating) if avg_rating else None,
            total_reviews=review_count
        )

    # ========================================================================
    # Cooking Logic (FIFO Consumption)
    # ========================================================================

    @staticmethod
    async def cook_recipe(
        recipe_id: int,
        request: CookRecipeRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> CookRecipeResponse:
        """
        Cook a recipe by consuming ingredients from fridge using FIFO.

        Process:
        1. Check user has access to fridge
        2. Get recipe requirements
        3. Check all ingredients available in fridge
        4. Consume each ingredient using FIFO logic
        5. Return consumption report
        """
        # Check fridge access
        await FridgeService._check_fridge_access(
            request.fridge_id, current_user_id, session
        )

        # Get recipe details
        recipe_detail = await RecipeService.get_recipe_detail(recipe_id, session)

        # Query all fridge items ONCE (fix N+1 query problem)
        all_items = await InventoryService.get_fridge_items(
            request.fridge_id, current_user_id, session
        )

        # Build ingredient → quantity map in memory
        ingredient_quantities = {}
        for item in all_items:
            if item.ingredient_id not in ingredient_quantities:
                ingredient_quantities[item.ingredient_id] = Decimal(0)
            ingredient_quantities[item.ingredient_id] += item.quantity

        # Check all ingredients available
        insufficient_ingredients = []
        for req in recipe_detail.requirements:
            available = ingredient_quantities.get(req.ingredient_id, Decimal(0))

            if available < req.quantity_needed:
                insufficient_ingredients.append(
                    f"{req.ingredient_name}: need {req.quantity_needed} {req.standard_unit}, "
                    f"have {available} {req.standard_unit}"
                )

        if insufficient_ingredients:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient ingredients: {', '.join(insufficient_ingredients)}"
            )

        # Consume ingredients using FIFO
        consumption_report = []
        for req in recipe_detail.requirements:
            from schemas.inventory import ConsumeRequest

            consume_req = ConsumeRequest(
                ingredient_id=req.ingredient_id,
                quantity=req.quantity_needed
            )

            consume_result = await InventoryService.consume_ingredient(
                request.fridge_id,
                consume_req,
                current_user_id,
                session
            )

            consumption_report.append({
                "ingredient": req.ingredient_name,
                "quantity": str(req.quantity_needed),
                "unit": req.standard_unit,
                "items_consumed": consume_result.items_consumed
            })

        # Log cooking action
        await BehaviorService.log_user_action(
            action_type="cook_recipe",
            user_id=current_user_id,
            resource_type="recipe",
            resource_id=str(recipe_id),
            metadata={
                "recipe_name": recipe_detail.recipe_name,
                "fridge_id": str(request.fridge_id),
                "ingredients_consumed": len(consumption_report)
            }
        )

        return CookRecipeResponse(
            recipe_name=recipe_detail.recipe_name,
            ingredients_consumed=consumption_report,
            success=True,
            message=f"Successfully cooked '{recipe_detail.recipe_name}' using FIFO ingredient consumption"
        )

    # ========================================================================
    # Reviews
    # ========================================================================

    @staticmethod
    async def create_review(
        recipe_id: int,
        request: ReviewCreateRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> None:
        """Create or update a recipe review."""
        # Verify recipe exists
        await RecipeService.get_recipe_detail(recipe_id, session)

        # Check if user already reviewed
        existing = await session.execute(
            select(RecipeReview).where(
                and_(
                    RecipeReview.user_id == current_user_id,
                    RecipeReview.recipe_id == recipe_id
                )
            )
        )
        existing_review = existing.scalar_one_or_none()

        if existing_review:
            # Update existing review
            existing_review.rating = request.rating
            existing_review.comment = request.comment
            existing_review.review_date = datetime.utcnow()
            session.add(existing_review)
        else:
            # Create new review
            new_review = RecipeReview(
                user_id=current_user_id,
                recipe_id=recipe_id,
                rating=request.rating,
                comment=request.comment,
                review_date=datetime.utcnow()
            )
            session.add(new_review)

        await session.commit()

    @staticmethod
    async def get_recipe_reviews(
        recipe_id: int,
        session: AsyncSession
    ) -> List[ReviewResponse]:
        """Get all reviews for a recipe."""
        result = await session.execute(
            select(RecipeReview, User)
            .join(User, RecipeReview.user_id == User.user_id)
            .where(RecipeReview.recipe_id == recipe_id)
            .order_by(RecipeReview.review_date.desc())
        )
        rows = result.all()

        reviews = []
        for review, user in rows:
            reviews.append(
                ReviewResponse(
                    user_id=review.user_id,
                    user_name=user.user_name,
                    recipe_id=review.recipe_id,
                    rating=review.rating,
                    comment=review.comment,
                    review_date=review.review_date
                )
            )

        return reviews

    # ========================================================================
    # Meal Planning
    # ========================================================================

    @staticmethod
    async def create_meal_plan(
        request: MealPlanCreateRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> MealPlan:
        """Schedule a recipe for a specific date."""
        # Verify recipe exists
        await RecipeService.get_recipe_detail(request.recipe_id, session)

        # Verify user has access to the fridge
        await FridgeService._check_fridge_access(
            request.fridge_id, current_user_id, session
        )

        # Create meal plan
        new_plan = MealPlan(
            user_id=current_user_id,
            recipe_id=request.recipe_id,
            fridge_id=request.fridge_id,
            planned_date=datetime.combine(request.planned_date, datetime.min.time())
        )
        session.add(new_plan)
        await session.commit()
        await session.refresh(new_plan)

        return new_plan

    @staticmethod
    async def get_meal_plans(
        current_user_id: UUID,
        session: AsyncSession,
        fridge_id: UUID = None,
        start_date: date = None,
        end_date: date = None
    ) -> List[MealPlanResponse]:
        """
        Get user's meal plans with optional filtering.

        - If fridge_id provided: verifies access and returns all plans for that fridge
        - If no fridge_id: returns all plans across all user's accessible fridges
        - Optional date range filtering
        """
        # Verify fridge access if fridge_id is specified
        if fridge_id:
            await FridgeService._check_fridge_access(
                fridge_id, current_user_id, session
            )

        query = (
            select(MealPlan, Recipe)
            .join(Recipe, MealPlan.recipe_id == Recipe.recipe_id)
            .where(MealPlan.user_id == current_user_id)
        )

        # Filter by fridge if specified
        if fridge_id:
            query = query.where(MealPlan.fridge_id == fridge_id)

        if start_date:
            query = query.where(MealPlan.planned_date >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.where(MealPlan.planned_date <= datetime.combine(end_date, datetime.max.time()))

        query = query.order_by(MealPlan.planned_date.asc())

        result = await session.execute(query)
        rows = result.all()

        plans = []
        for plan, recipe in rows:
            plans.append(
                MealPlanResponse(
                    plan_id=plan.plan_id,
                    user_id=plan.user_id,
                    recipe_id=plan.recipe_id,
                    recipe_name=recipe.recipe_name,
                    fridge_id=plan.fridge_id,
                    planned_date=plan.planned_date.date(),
                    status=plan.status
                )
            )

        return plans
