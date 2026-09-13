from django.db import models

from common.models import PublishableModel, PublishedManager, TimeStampedModel, UUIDPublicIDMixin


class AccessTier(models.TextChoices):
    """
    Drives entitlement checks (subscriptions app) — NOT a hardcoded
    "if game_count >= 3" rule. FREE games are always playable. TRIAL
    games count against the 3-distinct-games trial allowance. PREMIUM
    requires an active subscription.
    """

    FREE = "free", "Free"
    TRIAL = "trial", "Trial-eligible"
    PREMIUM = "premium", "Premium"


class Game(PublishableModel, TimeStampedModel, UUIDPublicIDMixin):
    """
    Metadata + configuration only. Django never renders the game —
    React/Canvas owns the mechanics. `config` is genuinely variable
    per game (level layouts, targets, reward tuning per level) so it's
    JSON on purpose, per the "don't abuse JSONB but don't avoid it
    where content really is unstructured" guidance. Anything that needs
    querying/filtering (topic, difficulty, access_tier) is still a real
    column, not buried inside the JSON.

    Example `config` shape (matches the Pizza Fraction Challenge the
    frontend already built):
    {
      "levels": [
        {"level": 1, "title": "Warm Up", "total_units": 4,
         "target": {"num": 1, "den": 4}, "reward_xp": 15, "reward_coins": 8}
      ]
    }
    """

    class GameType(models.TextChoices):
        FRACTION_PIZZA = "fraction_pizza", "Fraction pizza"
        SCIENCE_SIM = "science_sim", "Science simulation"
        MATCHING = "matching", "Matching game"
        OTHER = "other", "Other"

    concept = models.ForeignKey("curriculum.Concept", on_delete=models.CASCADE, related_name="games", null=True, blank=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    game_type = models.CharField(max_length=50, default="other", blank=True)
    difficulty = models.CharField(
        max_length=10,
        choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
        default="easy",
    )
    access_tier = models.CharField(max_length=10, choices=AccessTier.choices, default=AccessTier.FREE)
    config = models.JSONField(default=dict, blank=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        indexes = [models.Index(fields=["concept", "status"])]

    def __str__(self):
        return self.title


class GameSession(TimeStampedModel, UUIDPublicIDMixin):
    """
    One attempt at one game. `reward_granted` is the idempotency guard:
    the complete-session endpoint checks this flag inside a transaction
    before awarding anything, so a duplicate/retried request can never
    double-pay XP or coins (see gamification app + Phase 6 view logic).

    `client_result_payload` keeps the raw submission for audit/debugging
    even though we don't fully trust it — validated fields (score,
    accuracy) are still normal columns so they stay queryable.
    """

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="game_sessions")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="sessions")
    level = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)

    score = models.PositiveIntegerField(default=0)
    accuracy = models.FloatField(null=True, blank=True, help_text="0.0–1.0")
    time_spent_seconds = models.PositiveIntegerField(default=0)
    correct_actions = models.PositiveIntegerField(default=0)
    wrong_actions = models.PositiveIntegerField(default=0)

    client_result_payload = models.JSONField(null=True, blank=True)
    reward_granted = models.BooleanField(default=False)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["student", "game"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.student} · {self.game} · {self.status}"


class GameContent(TimeStampedModel):
    """
    Extensible content/questions belonging to a Game.
    Allows a Game to have multiple structured questions or levels
    without duplicating curriculum foreign keys (Game.concept remains the single authority).
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="contents")
    order = models.PositiveSmallIntegerField(default=1)
    prompt = models.CharField(max_length=255, blank=True, help_text="Question text or level objective")
    content_type = models.CharField(max_length=50, default="standard", help_text="e.g. read_number, build_number, quiz_choice, etc.")
    data = models.JSONField(default=dict, blank=True, help_text="Flexible game-specific payload (targets, options, assets)")
    correct_answer = models.JSONField(null=True, blank=True, help_text="Expected answer or rule for verification")
    points = models.PositiveIntegerField(default=10)
    hints = models.JSONField(default=list, blank=True, help_text="List of hints for students")

    class Meta:
        ordering = ["game", "order"]
        verbose_name = "game content / question"
        verbose_name_plural = "game contents / questions"

    def __str__(self):
        return f"{self.game.title} - Step {self.order}: {self.prompt or self.content_type}"

