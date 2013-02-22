from datetime import datetime
from seantis.dir.events.tests import FunctionalTestCase


class BrowserTestCase(FunctionalTestCase):

    def setUp(self):
        super(BrowserTestCase, self).setUp()

        self.baseurl = self.portal.absolute_url()

        browser = self.new_browser()
        browser.login_admin()

        # create an events directory
        browser.open(self.baseurl + '/++add++seantis.dir.events.directory')

        browser.getControl('Name').value = 'Veranstaltungen'
        browser.getControl(
            name='form.widgets.cat1_suggestions'
        ).value = "Category1"
        browser.getControl(
            name='form.widgets.cat2_suggestions'
        ).value = "Category2"
        browser.getControl('Save').click()

        self.assertTrue('Veranstaltungen' in browser.contents)

        # the directory needs to be published for the anonymous
        # user to submit events
        browser.open(
            browser.url + '/../content_status_modify?workflow_action=publish'
        )

        self.admin_browser = browser

    def tearDown(self):
        self.admin_browser.open(
            self.baseurl + '/veranstaltungen/delete_confirmation'
        )
        self.admin_browser.getControl('Delete').click()
        self.admin_browser.assert_notfound(self.baseurl + '/veranstaltungen')

    def test_workflow(self):

        baseurl = self.baseurl

        # anonymous browser
        fourchan = self.new_browser()
        fourchan.open(baseurl + '/veranstaltungen/@@submit')

        self.assertTrue('Send us your events' in fourchan.contents)

        # create some event
        def create_event():
            fourchan.getControl(name='form.widgets.title').value = 'Party'
            fourchan.getControl(
                name='form.widgets.short_description'
            ).value = 'Some Party'

            start = datetime.now().replace(hour=8)
            end = datetime.now().replace(hour=12)

            fourchan.set_date('form.widgets.start', start)
            fourchan.set_date('form.widgets.end', end)

            fourchan.getControl('Category1').selected = True
            fourchan.getControl('Category2').selected = True

            fourchan.getControl('Continue').click()
            self.assertTrue('preview' in fourchan.url)
            fourchan.getControl('Continue').click()
            self.assertTrue('finish' in fourchan.url)

            fourchan.getControl(
                name='form.widgets.submitter'
            ).value = 'John Doe'
            fourchan.getControl(
                name='form.widgets.submitter_email'
            ).value = 'john.doe@example.com'

            fourchan.getControl('Submit').click()

        create_event()

        # the event is now invisible to the anonymous user in the directory
        fourchan.open(baseurl + '/veranstaltungen?state=submitted')
        self.assertFalse('Some Party' in fourchan.contents)

        # it is however visible to the admin
        browser = self.admin_browser
        browser.open(baseurl + '/veranstaltungen?state=submitted')

        self.assertTrue('Some Party' in browser.contents)

        browser = self.admin_browser
        browser.open(baseurl + '/veranstaltungen?state=submitted')

        self.assertTrue('Some Party' in browser.contents)

        # unless the admin filters it out
        browser.open(baseurl + '/veranstaltungen?state=published')

        self.assertFalse('Some Party' in browser.contents)

        # who now has the chance to either deny or publish the event
        browser.open(baseurl + '/veranstaltungen?state=submitted')
        self.assertTrue('Publish' in browser.contents)
        self.assertTrue('Deny Publication' in browser.contents)
        self.assertTrue('Submitted' in browser.contents)

        # let's deny
        browser.getLink('Deny Publication').click()

        # the event should now be invisible to both admin and anonymous
        browser.open(baseurl + '/veranstaltungen')
        self.assertFalse('Some Party' in browser.contents)

        fourchan.open(browser.url)
        self.assertFalse('Some Party' in browser.contents)

        # let's repeat, but publish this time
        fourchan.open(baseurl + '/veranstaltungen/@@submit')
        create_event()

        browser.open(baseurl + '/veranstaltungen?state=submitted')
        browser.getLink('Publish', index=1).click()

        # this should've led to a state change
        browser.open(baseurl + '/veranstaltungen?state=published')
        self.assertTrue('Some Party' in browser.contents)
        self.assertTrue('Archive' in browser.contents)

        fourchan.open(browser.url)
        self.assertTrue('Some Party' in fourchan.contents)
        self.assertFalse('Archive' in fourchan.contents)

        # archiving the event should hide it again
        browser.getLink('Archive').click()
        browser.open(baseurl + '/veranstaltungen')

        self.assertFalse('Some Party' in browser.contents)

        fourchan.open(browser.url)
        self.assertFalse('SomeParty' in browser.contents)

    def test_preview(self):

        baseurl = self.baseurl

        # anonymous browser
        fourchan = self.new_browser()
        fourchan.open(baseurl + '/veranstaltungen/@@submit')

        self.assertTrue('Send us your events' in fourchan.contents)

        # create a recurring event
        fourchan.getControl(name='form.widgets.title').value = 'Recurring'
        fourchan.getControl(
            name='form.widgets.short_description'
        ).value = 'Every Day'
        fourchan.getControl(name='form.widgets.locality').value = 'at home'

        start = datetime.now().replace(hour=8)
        end = datetime.now().replace(hour=12)

        fourchan.set_date('form.widgets.start', start)
        fourchan.set_date('form.widgets.end', end)

        fourchan.getControl('Category1').selected = True
        fourchan.getControl('Category2').selected = True

        fourchan.getControl(
            name='form.widgets.recurrence'
        ).value = 'RRULE:FREQ=DAILY;COUNT=7'

        fourchan.getControl('Continue').click()
        self.assertTrue('preview' in fourchan.url)

        # expect all fields to be shown and the recurrence resulting in
        # a number of events in the list

        self.assertTrue('Recurring' in fourchan.contents)
        self.assertTrue('Every Day' in fourchan.contents)
        self.assertTrue('at home' in fourchan.contents)
        self.assertEqual(fourchan.contents.count('"eventgroup"'), 7)

        # update the recurrence and check back
        fourchan.getControl('Adjust').click()

        fourchan.getControl(
            name='form.widgets.recurrence'
        ).value = 'RRULE:FREQ=DAILY;COUNT=52'

        fourchan.getControl('Continue').click()

        self.assertEqual(fourchan.contents.count('"eventgroup"'), 52)

        # remove the recurrence, ensuring that one event remains
        fourchan.getControl('Adjust').click()

        fourchan.getControl(name='form.widgets.recurrence').value = ''
        fourchan.getControl('Continue').click()

        self.assertEqual(fourchan.contents.count('"eventgroup"'), 1)

        # ensure that no more than 52 occurrences may be entered
        fourchan.getControl('Adjust').click()

        fourchan.getControl(
            name='form.widgets.recurrence'
        ).value = 'RRULE:FREQ=DAILY;COUNT=53'

        fourchan.getControl('Continue').click()

        self.assertTrue(
            'You may not add more than 52 occurences' in fourchan.contents
        )

        # regression test for an issue where occurrences in the future
        # were not counted correctly
        fourchan.set_date('form.widgets.start', datetime(2020, 1, 1, 10, 0))
        fourchan.set_date('form.widgets.end', datetime(2020, 1, 1, 12, 0))

        fourchan.getControl(
            name='form.widgets.recurrence'
        ).value = 'RRULE:FREQ=DAILY;UNTIL=20200222T000000'

        fourchan.getControl('Continue').click()  # ok
        fourchan.getControl('Adjust').click()

        fourchan.getControl(
            name='form.widgets.recurrence'
        ).value = 'RRULE:FREQ=DAILY;UNTIL=20200223T000000'

        fourchan.getControl('Continue').click()  # not okay

        self.assertTrue(
            'You may not add more than 52 occurences' in fourchan.contents
        )

    def test_event_submission(self):

        browser = self.admin_browser
        baseurl = self.baseurl

        # get a browser for anonymous
        fourchan = self.new_browser()
        fourchan.open(baseurl + '/veranstaltungen')

        self.assertTrue('Veranstaltungen' in browser.contents)

        # get to the submit form
        fourchan.getLink('Submit Your Event').click()

        self.assertTrue('Send us your events' in fourchan.contents)

        fourchan.getControl(name='form.widgets.title').value = 'Stammtisch'
        fourchan.getControl(
            name='form.widgets.short_description'
        ).value = 'Socializing Yo'

        start = datetime.now().replace(hour=8)
        end = datetime.now().replace(hour=12)

        fourchan.set_date('form.widgets.start', start)
        fourchan.set_date('form.widgets.end', end)

        fourchan.getControl('Category1').selected = True
        fourchan.getControl('Category2').selected = True

        fourchan.getControl('Continue').click()

        # previewing an event should send us to the preview view
        self.assertTrue('preview' in fourchan.url)

        # a token should have been added to the url
        self.assertTrue('token=' in fourchan.url)

        # the preview should contain the entered information
        self.assertTrue('Socializing Yo' in fourchan.contents)

        # if the user tries to submit another event while this one is still
        # in preview, the existing event is loaded
        # (the form is turned into an edit form)
        oldurl = fourchan.url

        fourchan.open(baseurl + '/veranstaltungen/@@submit')
        self.assertEqual(
            fourchan.getControl(name='form.widgets.title').value,
            'Stammtisch'
        )
        self.assertEqual(
            fourchan.getControl(name='form.widgets.short_description').value,
            'Socializing Yo'
        )

        fourchan.open(oldurl)

        # there's a change-event button which submits a GET request to
        # the submit form using the token in the request
        fourchan.getControl('Adjust').click()
        self.assertTrue('submit?token=' in fourchan.url)
        self.assertFalse(fourchan.url.endswith('?token='))

        # we should be able to change some things
        # and come back to the url to find those changes

        fourchan.getControl(
            name='form.widgets.short_description'
        ).value = 'Serious Business'
        fourchan.getControl('Continue').click()

        self.assertTrue('Serious Business' in fourchan.contents)
        self.assertTrue('preview' in fourchan.url)

        # at the same time this event in preview is invisble in the list
        # even for administrators
        browser.open(baseurl + '/veranstaltungen')
        self.assertTrue('Veranstaltungen' in browser.contents)
        self.assertFalse('Serious Business' in browser.contents)

        # other anonymous users may not access the view or the preview
        google_robot = self.new_browser()
        google_robot.assert_notfound(baseurl + '/veranstaltungen/stammtisch')
        google_robot.assert_notfound(
            baseurl + '/veranstaltungen/stammtisch/preview'
        )

        # not event the admin at this point (not sure about that one yet)
        browser.assert_notfound(baseurl + '/veranstaltungen/stammtisch')
        browser.assert_notfound(
            baseurl + '/veranstaltungen/stammtisch/preview'
        )

        # if the user decides to cancel the event before submitting it, he
        # loses the right to access the event (will be cleaned up by cronjob)
        fourchan.getControl('Cancel').click()

        fourchan.assert_notfound(baseurl + '/veranstaltungen/stammtisch')
        fourchan.assert_notfound(
            baseurl + '/veranstaltungen/stammtisch/preview'
        )
        fourchan.assert_notfound(
            baseurl + '/veranstaltungen/stammtisch/edit-event'
        )

        # since we cancelled we must now create a new event to
        # test the submission process
        new = self.new_browser()
        new.open(baseurl + '/veranstaltungen/@@submit')

        self.assertEqual(new.getControl(name='form.widgets.title').value, '')
        self.assertEqual(
            new.getControl(name='form.widgets.short_description').value, ''
        )

        start = datetime.now().replace(hour=8)
        end = datetime.now().replace(hour=12)

        new.set_date('form.widgets.start', start)
        new.set_date('form.widgets.end', end)

        new.getControl('Category1').selected = True
        new.getControl('Category2').selected = True

        new.getControl(name='form.widgets.title').value = "Submitted Event"
        new.getControl(name='form.widgets.short_description').value = "YOLO"

        new.getControl('Continue').click()

        # at this point the event is invisble to the admin
        browser.open(baseurl + '/veranstaltungen?state=submitted')
        self.assertFalse('YOLO' in browser.contents)

        # until the anonymous user submits the event
        new.getControl('Continue').click()

        new.getControl('Submit').click()

        # at this point we 'forgot' to fill in the submitter info so we have at
        # it again and fix that
        new.getControl(name='form.widgets.submitter').value = 'John Doe'
        new.getControl(
            name='form.widgets.submitter_email'
        ).value = 'john.doe@example.com'

        new.getControl('Submit').click()

        browser.open(baseurl + '/veranstaltungen?state=submitted')
        self.assertTrue('YOLO' in browser.contents)

        # the user may no longer access the event at this point, though
        # it is no longer an inexistant resource
        new.assert_unauthorized(baseurl + '/veranstaltungen/submitted-event')

        # the admin should be able to see the submitter's name and email
        browser.open(baseurl + '/veranstaltungen/submitted-event')
        self.assertTrue('John Doe' in browser.contents)
        self.assertTrue('john.doe@example.com' in browser.contents)

        # once we publish it and open in another browser this information is
        # hidden from the public eye
        url = browser.url
        browser.open(baseurl + (
            '/veranstaltungen/submitted-event'
            '/content_status_modify?workflow_action=publish'
        ))

        public = self.new_browser()
        public.open(url)

        self.assertTrue('YOLO' in public.contents)
        self.assertFalse('John Doe' in public.contents)
        self.assertFalse('john.doe@example.com' in public.contents)

    def test_default_forms(self):

        # admins use the submit / preview forms for adding / editing
        # as well so we don't have to support two different form types
        # the following code tests that

        baseurl = self.baseurl
        browser = self.admin_browser

        browser.open(
            baseurl + '/veranstaltungen/++add++seantis.dir.events.item'
        )
        self.assertTrue('Send us your events' in browser.contents)

        browser.getControl(name='form.widgets.title').value = 'Add Test'
        browser.getControl(
            name='form.widgets.short_description'
        ).value = 'Add Test Description'

        start = datetime.now().replace(hour=8)
        end = datetime.now().replace(hour=12)

        browser.set_date('form.widgets.start', start)
        browser.set_date('form.widgets.end', end)

        browser.getControl('Category1').selected = True
        browser.getControl('Category2').selected = True

        browser.getControl('Continue').click()
        self.assertTrue('preview' in browser.url)

        self.assertTrue('Add Test Description' in browser.contents)

        browser.getControl('Continue').click()
        self.assertTrue('finish' in browser.url)

        browser.getControl('Submitter Name').value = 'Submitter'
        browser.getControl('Submitter Email').value = 'submit@example.com'

        browser.getControl('Submit').click()

        # show the submitted events
        browser.getLink('Submitted').click()

        self.assertTrue('Add Test Description' in browser.contents)
        self.assertTrue('Veranstaltungen' in browser.contents)

        browser.open(baseurl + '/veranstaltungen/add-test/edit')
        self.assertTrue('Send us your events' in browser.contents)

        browser.getControl(
            name='form.widgets.short_description'
        ).value = 'Changed Test Description'
        browser.getControl('Save Event').click()

        self.assertTrue('Changed Test Description' in browser.contents)
        self.assertFalse('preview' in browser.url)

    def test_recurrence(self):

        baseurl = self.baseurl
        browser = self.admin_browser

        browser.open(
            baseurl + '/veranstaltungen/++add++seantis.dir.events.item'
        )
        self.assertTrue('Send us your events' in browser.contents)

        browser.getControl(name='form.widgets.title').value = 'Recurring'
        browser.getControl(
            name='form.widgets.short_description'
        ).value = 'Add Test Description'
        browser.getControl(
            name='form.widgets.recurrence'
        ).value = 'RRULE:FREQ=DAILY;COUNT=7'

        start = datetime.now().replace(hour=8)
        end = datetime.now().replace(hour=12)

        browser.set_date('form.widgets.start', start)
        browser.set_date('form.widgets.end', end)

        browser.getControl('Category1').selected = True
        browser.getControl('Category2').selected = True

        browser.getControl('Continue').click()
        browser.getControl('Continue').click()

        browser.getControl('Submitter Name').value = 'Submitter'
        browser.getControl('Submitter Email').value = 'submit@example.com'

        browser.getControl('Submit').click()

        # make sure to get all events
        browser.getLink('This and Next Year').click()

        # with the state submitted
        browser.getLink('Submitted').click()

        # take the last occurrence
        first_url = browser.getLink('Recurring', index=0).url
        link = browser.getLink('Recurring', index=6)
        year, month, day = map(
            int, link.url[len(link.url) - 10:].split('-')
        )

        # and ensure that the date is correct in the detail view
        link.click()

        self.assertFalse('Today' in browser.contents)
        self.assertTrue('%02i.%02i' % (day, month) in browser.contents)

        browser.open(first_url)
        self.assertTrue('Today' in browser.contents)

    def test_terms(self):

        baseurl = self.baseurl
        browser = self.admin_browser

        def enable_terms(enable):
            new = self.new_browser()
            new.login_admin()

            new.open(baseurl + '/veranstaltungen/edit')
            new.getControl(
                name="form.widgets.terms"
            ).value = enable and 'verily, though agreeth' or ''
            new.getControl('Save').click()

        browser.open(
            baseurl + '/veranstaltungen/++add++seantis.dir.events.item'
        )
        self.assertTrue('Send us your events' in browser.contents)

        browser.getControl(name='form.widgets.title').value = 'Test'
        browser.getControl(
            name='form.widgets.short_description'
        ).value = 'Test'

        start = datetime.now().replace(hour=8)
        end = datetime.now().replace(hour=12)

        browser.set_date('form.widgets.start', start)
        browser.set_date('form.widgets.end', end)

        browser.getControl('Category1').selected = True
        browser.getControl('Category2').selected = True

        browser.getControl('Continue').click()
        browser.getControl('Continue').click()

        self.assertFalse('Terms and Conditions' in browser.contents)

        enable_terms(True)

        browser.reload()
        self.assertTrue('Terms and Conditions' in browser.contents)

        browser.getLink('Terms and Conditions').click()
        self.assertTrue('verily' in browser.contents)

        browser.goBack()

        # if not agreed upon, the submission is denied
        browser.getControl('Submitter Name').value = 'Submitter'
        browser.getControl('Submitter Email').value = 'submit@example.com'
        self.assertTrue('Terms and Conditions' in browser.contents)

        browser.getControl('Submit').click()
        self.assertTrue('finish' in browser.url)
        self.assertTrue('Terms and Conditions' in browser.contents)

        browser.getControl(name='form.widgets.agreed:list').value = 'selected'
        browser.getControl('Submit').click()

        self.assertFalse('finish' in browser.url)
        self.assertFalse('Terms and Conditions' in browser.contents)
        self.assertTrue('Event submitted' in browser.contents)
