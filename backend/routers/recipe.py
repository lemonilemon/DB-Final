from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from core.dependencies import get_current_user_id, get_optional_user
from models.user import User
from schemas.recipe import (
    RecipeCreateRequest,
    RecipeBasicResponse,
    RecipeDetailResponse,
    CookRecipeRequest,
    CookRecipeResponse,
    ReviewCreateRequest,
    ReviewResponse,
    MealPlanCreateRequest,
    MealPlanResponse,
    MessageResponse,
)
from services.recipe_service import RecipeService
from services.behavior_service import BehaviorService


router = APIRouter(prefix="/api/recipes", tags=["Recipes"])


# ============================================================================
# Recipe Endpoints
# ============================================================================

@router.post(
    "",
    response_model=RecipeBasicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new recipe"
)
async def create_recipe(
    request: RecipeCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new recipe with ingredients and cooking steps.

    - Specify required ingredients with quantities
    - Add step-by-step instructions
    - Recipes are published immediately
    """
    recipe = await RecipeService.create_recipe(request, current_user_id, session)

    # Get full response
    recipes = await RecipeService.get_all_recipes(session)
    created = next(r for r in recipes if r.recipe_id == recipe.recipe_id)
    return created


@router.get(
    "",
    response_model=List[RecipeBasicResponse],
    summary="List all recipes"
)
async def list_recipes(
    search: Optional[str] = Query(None, description="Search by recipe name"),
    session: AsyncSession = Depends(get_session),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all recipes with ratings.

    - Sorted by newest first
    - Shows average rating and review count
    - Optional search by name
    """
    results = await RecipeService.get_all_recipes(session, search)

    # Log search if query was provided
    if search and user:
        await BehaviorService.log_search_query(
            query_type="recipe",
            query_text=search,
            results_count=len(results),
            user_id=user.user_id
        )

    return results


@router.get(
    "/{recipe_id}",
    response_model=RecipeDetailResponse,
    summary="Get recipe details"
)
async def get_recipe(
    recipe_id: int,
    session: AsyncSession = Depends(get_session),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Get detailed recipe with ingredients, steps, and ratings.

    - Shows all required ingredients with quantities
    - Step-by-step cooking instructions
    - Average rating from reviews
    """
    user_id = user.user_id if user else None
    return await RecipeService.get_recipe_detail(recipe_id, session, user_id)


@router.post(
    "/{recipe_id}/cook",
    response_model=CookRecipeResponse,
    summary="Cook recipe (FIFO consumption)"
)
async def cook_recipe(
    recipe_id: int,
    request: CookRecipeRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Cook a recipe by consuming ingredients from your fridge.

    **Uses FIFO logic:**
    - Automatically consumes ingredients from earliest expiry first
    - Checks all ingredients are available before cooking
    - Returns detailed consumption report

    **Example:**
    - Recipe needs 4 eggs, 50ml milk
    - Fridge has eggs expiring Dec 8 and Dec 12
    - System uses eggs from Dec 8 first (FIFO)
    """
    return await RecipeService.cook_recipe(
        recipe_id, request, current_user_id, session
    )


# ============================================================================
# Review Endpoints
# ============================================================================

@router.post(
    "/{recipe_id}/reviews",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Review a recipe"
)
async def create_review(
    recipe_id: int,
    request: ReviewCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Create or update your review for a recipe.

    - Rating: 1-5 stars
    - Optional comment
    - Can update existing review
    """
    await RecipeService.create_review(recipe_id, request, current_user_id, session)

    return MessageResponse(
        message="Review submitted successfully",
        detail=f"Rated {request.rating} stars"
    )


@router.get(
    "/{recipe_id}/reviews",
    response_model=List[ReviewResponse],
    summary="Get recipe reviews"
)
async def get_reviews(
    recipe_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Get all reviews for a recipe.

    - Sorted by newest first
    - Shows reviewer name, rating, and comment
    """
    return await RecipeService.get_recipe_reviews(recipe_id, session)


# ============================================================================
# Meal Planning Endpoints
# ============================================================================

meal_plan_router = APIRouter(prefix="/api/meal-plans", tags=["Meal Planning"])


@meal_plan_router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a recipe"
)
async def create_meal_plan(
    request: MealPlanCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Schedule a recipe for a specific date.

    - Plan your meals in advance
    - Can schedule same recipe multiple times
    """
    plan = await RecipeService.create_meal_plan(request, current_user_id, session)

    return MessageResponse(
        message="Meal scheduled successfully",
        detail=f"Plan ID: {plan.plan_id}"
    )


@meal_plan_router.get(
    "",
    response_model=List[MealPlanResponse],
    summary="View meal plans"
)
async def get_meal_plans(
    fridge_id: Optional[UUID] = Query(None, description="Filter by fridge"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Get your scheduled meals.

    - Optional fridge filtering (all your fridges if not specified)
    - Optional date range filtering
    - Sorted by date (earliest first)
    """
    return await RecipeService.get_meal_plans(
        current_user_id, session, fridge_id, start_date, end_date
    )
