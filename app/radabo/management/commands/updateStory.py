from django.core.management.base import BaseCommand, CommandError
from radabo.models import Story, Session
from radabo.utils import getStory, createStory, updateStory, initRally
from django.utils import timezone
from django.db.models import Q
import sys

"""
This command will sync the local Story objects with User Story data from Rally.
"""
class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        # Starts a session, which is updated on every story.  This is used to
        # identify stories not pulled from Rally, but still in the DB.  These
        # are often stories deleted from the backlog.
        session=Session()
        session.save()

        rallyServer = initRally()

        # Queries enhancements not yet released OR project grooming stories
        # not in Completed Archive status
        # Not splitting this line in case it breaks Rally's picky formatting
        q='(Feature.Parent.FormattedID = "E258") AND (((Feature.FormattedID != "F3841") AND (Release = "")) OR ((Feature.FormattedID = "F3841") AND (c_ITFinanceConsultingKanbanState != "Completed Archive")))'

        f="FormattedID,ObjectID,Name,Description,PlanEstimate," \
          "c_BusinessValueBV,ScheduleStatePrefix,c_Module,Project," \
          "Feature,c_SolutionSize,c_Stakeholders,Iteration,Release," \
          "Tags,RevisionHistory,c_Theme,Blocked,BlockedReason," \
          "CreationDate,c_Region,Ready"

        response = rallyServer.get(
                       'UserStory',
                       query=q,
                       fetch=f,
                       order="FormattedID"
                   )

        # Uh oh!
        if response.resultCount == 0:
            print "Cannot find any stories in the backlog!"
            print response.errors
            sys.exit(1)

        for story in response:
            """
            Horrible hack for the fact that referencing 
            Feature.Parent.FormattedID throws an error
            """
            story.Feature.Parent.FormattedID = "E258"
            try:
                this=getStory(story.FormattedID)
                if this:
                    # Update existing story
                    updateStory(this, story, session)
                else:
                    # Create a new story
                    createStory(story, session)
            except Exception as e:
                print "Failure to save story %s: %s" % (
                    story.FormattedID, str(e))
                sys.exit(2)

        # Query items not already updated in this session and update/delete
        stories = Story.objects.filter(
              ~Q(session=session) | Q(session__isnull=True), 
              Q(release__status__in=['Active','Planning']) | Q(release=None))

        for this in stories:
 
            q = ['FormattedId = "%s"' % this.rallyNumber]
            f += ',c_ITFinanceConsultingKanbanState'
            response = rallyServer.get(
                           'UserStory',
                           query=q,
                           fetch=f
                       )

            if response.resultCount == 0:
                print "Deleting %s" % (this.rallyNumber)
                this.delete()
            else:
                for story in response:
                    if story.c_ITFinanceConsultingKanbanState == \
                        "Completed Archive":
                        # Log fact story is deleted
                        print "Deleting archived story %s" % (story.FormattedID)
                    else:
                        updateStory(this, story, session)

        session.close()
