from django.shortcuts import redirect
from django.contrib.auth import get_user_model, login
from django.views import View

User = get_user_model()


class DemoLoginView(View):
    def get(self, request):
        demo_user = User.objects.filter(email__iexact="demo@tezmindz.com").first()
        created = demo_user is None
        if created:
            demo_user = User.objects.create_user(
                username="demo_student",
                email="demo@tezmindz.com",
                first_name="Demo Student",
                role=User.Role.STUDENT,
            )

        if created:
            demo_user.set_unusable_password()
            demo_user.save(update_fields=["password"])

        if not demo_user.is_active:
            demo_user.is_active = True
            demo_user.save(update_fields=["is_active"])

        login(request, demo_user)
        return redirect("/dashboard/")