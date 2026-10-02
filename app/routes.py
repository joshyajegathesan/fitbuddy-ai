from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    Request,
)

from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates

from .database import (
    get_all_users_with_plans,
    get_plan,
    get_user,
    save_plan,
    save_user,
    update_plan,
)

from .gemini_flash_generator import (
    generate_nutrition_tip_with_flash
)

from .gemini_generator import (
    generate_workout_gemini
)

from .schemas import (
    FeedbackRequest,
    UserInput,
)

from .updated_plan import (
    update_workout_plan
)


BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

router = APIRouter()


def render_error(
    request: Request,
    message: str,
    status_code: int = 400
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "error": message
        },
        status_code=status_code,
    )


@router.get(
    "/",
    response_class=HTMLResponse
)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "error": None
        }
    )


@router.post(
    "/generate-workout",
    response_class=HTMLResponse
)
def generate_workout(
    request: Request,

    username: str = Form(...),

    user_id: str = Form(...),

    age: int = Form(...),

    weight: float = Form(...),

    goal: str = Form(...),

    intensity: str = Form(...),
):

    try:

        data = UserInput(
            username=username,
            user_id=user_id,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )

    except Exception as exc:

        return render_error(
            request,
            str(exc),
            422
        )

    try:

        workout_plan = generate_workout_gemini(
            data.username,
            data.age,
            data.weight,
            data.goal,
            data.intensity,
        )

        nutrition_tip = (
            generate_nutrition_tip_with_flash(
                data.goal,
                data.age
            )
        )

        save_user(
            data.model_dump()
        )

        save_plan(
            data.user_id,
            workout_plan,
            nutrition_tip
        )

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": data,
                "workout_plan": workout_plan,
                "nutrition_tip": nutrition_tip,
                "updated": False,
                "message": None,
            },
        )

    except Exception as exc:

        return render_error(
            request,
            f"AI generation failed: {exc}",
            502
        )


@router.post(
    "/submit-feedback",
    response_class=HTMLResponse
)
def submit_feedback(
    request: Request,

    user_id: str = Form(...),

    feedback: str = Form(...),
):

    try:

        request_data = FeedbackRequest(
            user_id=user_id,
            feedback=feedback
        )

    except Exception as exc:

        return render_error(
            request,
            str(exc),
            422
        )

    user = get_user(
        request_data.user_id
    )

    plan = get_plan(
        request_data.user_id
    )

    if not user or not plan:

        return render_error(
            request,
            "User ID not found. Generate a plan first.",
            404
        )

    try:

        revised_plan = update_workout_plan(
            plan.original_plan,
            request_data.feedback,
            user.goal,
            user.intensity,
            user.age,
        )

        nutrition_tip = (
            generate_nutrition_tip_with_flash(
                user.goal,
                user.age
            )
        )

        update_plan(
            request_data.user_id,
            revised_plan,
            request_data.feedback,
            nutrition_tip
        )

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "workout_plan": revised_plan,
                "nutrition_tip": nutrition_tip,
                "updated": True,
                "message": (
                    "Your plan has been updated "
                    "using your feedback."
                ),
            },
        )

    except Exception as exc:

        return render_error(
            request,
            f"AI update failed: {exc}",
            502
        )


@router.get(
    "/view-all-users",
    response_class=HTMLResponse
)
def view_all_users(request: Request):

    users = get_all_users_with_plans()

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "users": users
        }
    )


@router.get("/health")
def health():

    return {
        "status": "ok",
        "service": "FitBuddy"
    }