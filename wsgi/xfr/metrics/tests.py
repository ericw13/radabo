from django.test import TestCase
from metrics.models import Sprint, Release, Story, Session, Module
from django.utils import timezone
from datetime import timedelta
from metrics.utils import getCurrentRelease, getRelease, getCurrentSprint, getSprint, getSolutionSize, getFeatureDesc, getStory

# Create your tests here.

class ReleaseTest(TestCase):

    def setUp(self):
        self.relName = "Test Release"
        self.badName = "FOO"
        r=Release.objects.create(name=self.relName,
                                 startDate=timezone.now() + timedelta(days=-7),
                                 endDate=timezone.now() + timedelta(days=7))

    def test_get_release(self):
        r=getRelease(self.relName)
        x = (r != None)
        self.assertEqual(x,True)

    def test_get_current_release(self):
        t=timezone.now()
        r=getCurrentRelease()
        x = r.startDate <= t and r.endDate >= t
        self.assertEqual(x, True)

    def test_neg_get_release(self):
        r=getRelease(self.badName)
        self.assertEqual(r, None)

class SprintTest(TestCase):

    def setUp(self):
        self.sprintName = "Test Sprint"
        self.badName = "FOO"
        s=Sprint.objects.create(name=self.sprintName,
                                startDate=timezone.now() + timedelta(days=-7),
                                endDate=timezone.now() + timedelta(days=7),
                                velocity=100)

    def test_get_sprint(self):
        s=getSprint(self.sprintName)
        x = (s != None)
        self.assertEqual(x, True)

    def test_get_current_sprint(self):
        t=timezone.now()
        s=getCurrentSprint()
        x= s.startDate <= t and s.endDate >= t
        self.assertEqual(x,True)

    def test_neg_get_sprint(self):
        r=getSprint(self.badName)
        self.assertEqual(r, None)

class ModuleTest(TestCase):

    def setUp(self):
        self.moduleName = "Test Module"
        self.badName = "FOO"
        m=Module.objects.create(moduleName = self.moduleName,
                                track = 'OTC',
                                globalLead = 'Eric Wright')

    def test_get_module(self):
        m=Module.objects.filter(moduleName=self.moduleName)
        self.assertEqual(len(m),1)

    def neg_test_get_module(self):
        m=Module.objects.filter(moduleName=self.badName)
        self.assertEqual(m, None)

class UtilTest(TestCase):

    def setUp(self):
        self.defaultText = "Test"

    def test_get_solution_size_small(self):
        x = getSolutionSize(1, self.defaultText)
        self.assertEqual(x, "Small")

    def test_get_solution_size_med(self):
        x = getSolutionSize(5, self.defaultText)
        self.assertEqual(x, "Medium")

    def test_get_solution_size_large(self):
        x = getSolutionSize(13, self.defaultText)
        self.assertEqual(x, "Large")

    def test_get_solution_size_unknown1(self):
        x = getSolutionSize(None, self.defaultText)
        self.assertEqual(x, self.defaultText)

    def test_get_solution_size_unknown2(self):
        x = getSolutionSize(None, None)
        self.assertEqual(x, "Unknown")

    def test_get_feature_desc_e(self):
        x = getFeatureDesc("F1467")
        self.assertEqual(x, "Feature")

    def test_get_feature_desc_pg(self):
        x = getFeatureDesc("F3841")
        self.assertEqual(x, "Project Grooming")

    def test_get_feature_desc_e(self):
        x = getFeatureDesc("F1234")
        self.assertEqual(x, "Project Deliverable")

class StoryTest(TestCase):

    def setUp(self):
        self.goodNumber = "US12345"
        self.badNumber = "US54321"
        x=Story.objects.create(rallyNumber=self.goodNumber,
                               description="This is a test story",
                               points=8,
                               businessValue=13)

    def test_get_story(self):
        s=getStory(self.goodNumber)
        x = (s != None)
        self.assertEqual(x, True)

    def neg_test_get_story(self):
        s=getStory(self.badNumber)
        self.assertEqual(s, None)
