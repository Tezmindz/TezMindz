from django.utils import timezone

from .models import Subscription, TrialGameLog


def can_student_access_game(student, game):
    """
    Return True if the student is entitled to access the game.
    """

    # Free games are available to authenticated students.
    if game.access_tier == "free":
        return True

    # Trial games:
    # - A previously used trial game can be replayed.
    # - A new trial game is allowed while the student has used fewer
    #   than the configured number of distinct trial games.
    if game.access_tier == "trial":
        already_used = TrialGameLog.objects.filter(
            student=student,
            game=game,
        ).exists()

        if already_used:
            return True

        trial_games_used = TrialGameLog.objects.filter(
            student=student
        ).count()

        return trial_games_used < 3

    # Premium games require an active subscription.
    if game.access_tier == "premium":
        return Subscription.objects.filter(
            student=student,
            status="active",
        ).exists()

    return False