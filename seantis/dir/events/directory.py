from five import grok
from plone.namedfile.field import NamedImage

from seantis.dir.base import directory
from seantis.dir.base.interfaces import IDirectory
from seantis.dir.events import _

class IEventsDirectory(IDirectory):
    """Extends the seantis.dir.base.directory.IDirectory"""

    image = NamedImage(
            title=_(u'Image'),
            required=False,
            default=None
        )

IEventsDirectory.setTaggedValue('seantis.dir.base.omitted', 
    ['cat1', 'cat2', 'cat3', 'cat4']
)

class EventsDirectory(directory.Directory):
    
    def labels(self):
        return dict(cat1=_(u'What'), cat2=_(u'Where'))

    def used_categories(self):
        return ('cat1', 'cat2')

    def unused_categories(self):
        return ('cat3', 'cat4')

class ExtendedDirectoryViewlet(grok.Viewlet):
    grok.context(IEventsDirectory)
    grok.name('seantis.dir.events.directory.detail')
    grok.require('zope2.View')
    grok.viewletmanager(directory.DirectoryViewletManager)

    template = grok.PageTemplateFile('templates/directorydetail.pt')

class EventsDirectoryView(directory.View):

    grok.name('view')
    grok.context(IEventsDirectory)
    grok.require('zope2.View')

    template = grok.PageTemplateFile('templates/directory.pt')