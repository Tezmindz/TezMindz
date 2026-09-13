from django.test import TestCase
from django.urls import reverse
from apps.curriculum.models import Grade, Subject, Topic, Concept
from apps.games.models import Game

class CurriculumFlowViewTests(TestCase):
    def setUp(self):
        self.grade = Grade.objects.create(name="Grade 4", order=4)
        self.subject = Subject.objects.create(name="Mathematics", slug="mathematics")
        self.topic = Topic.objects.create(subject=self.subject, grade=self.grade, title="Fractions")
        self.concept = Concept.objects.create(topic=self.topic, title="Fraction Pizza", content_body="Learn fractions")
        self.game = Game.objects.create(concept=self.concept, title="Pizza Fraction Challenge", access_tier="trial")

    def test_dashboard_page(self):
        response = self.client.get(reverse('common:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_subject_page(self):
        response = self.client.get(reverse('common:subject', args=[self.subject.id]))
        self.assertEqual(response.status_code, 200)

    def test_chapter_page(self):
        response = self.client.get(reverse('common:chapter', args=[self.topic.id]))
        self.assertEqual(response.status_code, 200)

    def test_concept_page(self):
        response = self.client.get(reverse('common:concept', args=[self.concept.id]))
        self.assertEqual(response.status_code, 200)
