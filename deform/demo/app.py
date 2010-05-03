# -*- coding: utf-8 -*-

""" A repoze.bfg app that demonstrates various Deform widgets and
capabilities """

import inspect
import sys

from webob import Response
from pkg_resources import resource_filename

from repoze.bfg.configuration import Configurator
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.i18n import get_localizer
from repoze.bfg.i18n import get_locale_name
from repoze.bfg.threadlocal import get_current_request
from repoze.bfg.view import bfg_view

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

import deform
import colander

from translationstring import TranslationStringFactory

_ = TranslationStringFactory('deform')
css = HtmlFormatter().get_style_defs('.highlight')

def translator(term):
    return get_localizer(get_current_request()).translate(term)

deform_template_dir = resource_filename('deform', 'templates/')

deform.Form.set_zpt_renderer(
    deform_template_dir,
    translator=translator,
    )

class demonstrate(object):
    def __init__(self, title):
        self.title = title

    def __call__(self, method):
        method.demo = self.title
        return method

class DeformDemo(object):
    def __init__(self, request):
        self.request = request
        self.macros = get_template('templates/main.pt').macros

    def render_form(self, form, appstruct=None, submitted='submit',
                    success=None, readonly=False):
        captured = None
        if submitted in self.request.POST:
            # the request represents a form submission
            try:
                # try to validate the submitted values
                controls = self.request.POST.items()
                captured = form.validate(controls)
                if success:
                    success()
                html = form.render(captured)
            except deform.ValidationFailure, e:
                # the submitted values could not be validated
                html = e.render()
        else:
            # the request requires a simple form rendering
            html = form.render(appstruct, readonly=readonly)

        code, start, end = self.get_code(2)

        # values passed to template for rendering
        return {
            'form':html,
            'captured':repr(captured),
            'code': code,
            'start':start,
            'end':end,
            'title':self.get_title(),
            }

    def get_code(self, level):
        frame = sys._getframe(level)
        lines, start = inspect.getsourcelines(frame.f_code)
        end = start + len(lines)
        code = ''.join(lines)
        code = unicode(code, 'utf-8')
        formatter = HtmlFormatter()
        return highlight(code, PythonLexer(), formatter), start, end

    @bfg_view(name='allcode', renderer='templates/code.pt')
    def allcode(self):
        params = self.request.params
        start = params.get('start')
        end = params.get('end')
        hl_lines = None
        if start and end:
            start = int(start)
            end = int(end)
            hl_lines = list(range(start, end))
        code = open(inspect.getsourcefile(self.__class__), 'r').read()
        code = code.decode('utf-8')
        formatter = HtmlFormatter(linenos='table', lineanchors='line',
                                  hl_lines=hl_lines)
        html = highlight(code, PythonLexer(), formatter)
        return {'code':html}

    def get_title(self):
        # gross hack; avert your eyes
        frame = sys._getframe(3)
        attr = frame.f_locals['attr']
        inst = frame.f_locals['inst']
        method = getattr(inst, attr)
        return method.demo

    @bfg_view(name='pygments.css')
    def cssview(self):
        response =  Response(body=css, content_type='text/css')
        response.cache_expires = 360
        return response

    @bfg_view(renderer='templates/index.pt')
    def index(self):
        def predicate(value):
            if getattr(value, 'demo', None) is not None:
                return True
        demos = inspect.getmembers(self, predicate)
        return {
            'demos':sorted([(method.demo, name) for name, method in demos])
            }

    @bfg_view(renderer='templates/form.pt', name='textinput')
    @demonstrate('Text Input Widget')
    def textinput(self):
        class Schema(deform.Schema):
            text = deform.SchemaNode(deform.String(),
                                     validator=colander.Length(max=100),
                                     description='Enter some text')
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['text'].widget = deform.widget.TextInputWidget(size=60)
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='textarea')
    @demonstrate('Text Area Widget')
    def textarea(self):
        class Schema(deform.Schema):
            text = deform.SchemaNode(deform.String(),
                                     validator=colander.Length(max=100),
                                     description='Enter some text')
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['text'].widget = deform.widget.TextAreaWidget(rows=10, cols=60)
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='password')
    @demonstrate('Password Widget')
    def password(self):
        class Schema(deform.Schema):
            password = deform.SchemaNode(
                deform.String(),
                validator=colander.Length(min=5, max=100),
                description='Enter a password')
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['password'].widget = deform.widget.PasswordWidget(size=20)
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='checkbox')
    @demonstrate('Checkbox Widget')
    def checkbox(self):
        class Schema(deform.Schema):
            want = deform.SchemaNode(
                deform.Boolean(),
                description='Check this box!',
                title='I Want It!')
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['want'].widget = deform.widget.CheckboxWidget()
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='radiochoice')
    @demonstrate('Radio Choice Widget')
    def radiochoice(self):
        choices = (('habanero', 'Habanero'), ('jalapeno', 'Jalapeno'),
                   ('chipotle', 'Chipotle'))
        class Schema(deform.Schema):
            pepper = deform.SchemaNode(
                deform.String(),
                validator=colander.OneOf([x[0] for x in choices]),
                title='Choose your pepper',
                description='Select a Pepper')
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['pepper'].widget = deform.widget.RadioChoiceWidget(values=choices)
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='checkedinput')
    @demonstrate('Checked Input Widget')
    def checkedinput(self):
        class Schema(deform.Schema):
            email = deform.SchemaNode(
                deform.String(),
                title='Email Address',
                description='Type your email address and confirm it',
                validator=colander.Email())
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['email'].widget = deform.widget.CheckedInputWidget(
            subject='Email',
            confirm_subject='Confirm Email',
            size=40)
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='checkedpassword')
    @demonstrate('Checked Password Widget')
    def checkedpassword(self):
        class Schema(deform.Schema):
            password = deform.SchemaNode(
                deform.String(),
                validator=colander.Length(min=5),
                description='Type your password and confirm it')
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['password'].widget = deform.widget.CheckedPasswordWidget(size=20)
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='mapping')
    @demonstrate('Mapping Widget')
    def mapping(self):
        class Mapping(deform.Schema):
            name = deform.SchemaNode(
                deform.String(),
                description='Content name')
            date = deform.SchemaNode(
                deform.Date(),
                description='Content date')
        class Schema(deform.Schema):
            number = deform.SchemaNode(
                deform.Integer())
            mapping = Mapping()
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='sequence_of_fileuploads')
    @demonstrate('Sequence of File Upload Widgets')
    def sequence_of_fileuploads(self):
        class Sequence(deform.SequenceSchema):
            upload = deform.SchemaNode(deform.FileData())
        class Schema(deform.Schema):
            uploads = Sequence()
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['uploads']['upload'].widget = deform.widget.FileUploadWidget(
            tmpstore)
        return self.render_form(form, success=tmpstore.clear)

    @bfg_view(renderer='templates/form.pt',
              name='sequence_of_fileuploads_with_initial_item')
    @demonstrate('Sequence of File Upload Widgets (With Initial Item)')
    def sequence_of_fileuploads_with_initial_item(self):
        class Sequence(deform.SequenceSchema):
            upload = deform.SchemaNode(deform.FileData())
        class Schema(deform.Schema):
            uploads = Sequence()
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['uploads'].widget = deform.widget.SequenceWidget(
            render_initial_item=True)
        form['uploads']['upload'].widget = deform.widget.FileUploadWidget(
            tmpstore)
        return self.render_form(form, success=tmpstore.clear)

    @bfg_view(renderer='templates/form.pt', name='sequence_of_mappings')
    @demonstrate('Sequence of Mapping Widgets')
    def sequence_of_mappings(self):
        class Mapping(deform.Schema):
            name = deform.SchemaNode(deform.String())
            title = deform.SchemaNode(deform.String())
        class Sequence(deform.SequenceSchema):
            mapping = Mapping()
        class Schema(deform.Schema):
            mappings = Sequence()
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt',
              name='sequence_of_mappings_with_initial_item')
    @demonstrate('Sequence of Mapping Widgets (With Initial Item)')
    def sequence_of_mappings_with_initial_item(self):
        class Mapping(deform.Schema):
            name = deform.SchemaNode(deform.String())
            title = deform.SchemaNode(deform.String())
        class Sequence(deform.SequenceSchema):
            mapping = Mapping()
        class Schema(deform.Schema):
            mappings = Sequence()
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['mappings'].widget = deform.widget.SequenceWidget(
            render_initial_item=True)
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt',
              name='readonly_sequence_of_mappings')
    @demonstrate('Read-Only Sequence of Mappings')
    def readonly_sequence_of_mappings(self):
        class Mapping(deform.Schema):
            name = deform.SchemaNode(deform.String())
            title = deform.SchemaNode(deform.String())
        class Sequence(deform.SequenceSchema):
            mapping = Mapping()
        class Schema(deform.Schema):
            mappings = Sequence()
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        return self.render_form(
            form,
            appstruct={'mappings':
                       [
                           {'name':'name1', 'title':'title1'},
                           {'name':'name2', 'title':'title2'},
                        ]
                       },
            readonly=True)

    @bfg_view(renderer='templates/form.pt', name='sequence_of_sequences')
    @demonstrate('Sequence of Sequence Widgets')
    def sequence_of_sequences(self):
        class NameAndTitle(deform.Schema):
            name = deform.SchemaNode(deform.String())
            title = deform.SchemaNode(deform.String())
        class NamesAndTitles(deform.SequenceSchema):
            name_and_title = NameAndTitle(title='Name and Title')
        class NamesAndTitlesSequences(deform.SequenceSchema):
            names_and_titles = NamesAndTitles(title='Names and Titles')
        class Schema(deform.Schema):
            names_and_titles_sequence = NamesAndTitlesSequences(
                title='Sequence of Sequences of Names and Titles')
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        outer = form['names_and_titles_sequence']
        outer.widget = deform.widget.SequenceWidget(
            render_initial_item=True)
        outer['names_and_titles'].widget = deform.widget.SequenceWidget(
            render_initial_item=True)
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='file')
    @demonstrate('File Upload Widget')
    def file(self):
        class Schema(deform.Schema):
            upload = deform.SchemaNode(deform.FileData())
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['upload'].widget = deform.widget.FileUploadWidget(tmpstore)
        return self.render_form(form, success=tmpstore.clear)

    @bfg_view(renderer='templates/form.pt', name='date')
    @demonstrate('Date Parts Widget')
    def date(self):
        import datetime
        from colander import Range
        class Schema(deform.Schema):
            date = deform.SchemaNode(
                deform.Date(),
                validator=Range(
                    min=datetime.date(2010, 1, 1),
                    min_err=_('${min} is earlier than earliest date ${val}')
                    )
                )
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='edit')
    @demonstrate('Edit Form')
    def edit(self):
        class Mapping(deform.Schema):
            name = deform.SchemaNode(
                deform.String(),
                description='Content name')
            date = deform.SchemaNode(
                deform.Date(),
                description='Content date')
        class Schema(deform.Schema):
            number = deform.SchemaNode(
                deform.Integer())
            mapping = Mapping()
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        import datetime
        # We don't need to suppy all the values required by the schema
        # for an initial rendering, only the ones the app actually has
        # values for.  Notice below that we don't pass the ``name``
        # value specified by the ``Mapping`` schema.
        appstruct = {
            'number':42,
            'mapping': {
                'date':datetime.date(2010, 4, 9),
                }
            }
        return self.render_form(form, appstruct=appstruct)

    @bfg_view(renderer='templates/form.pt', name='interfield')
    @demonstrate('Inter-Field Validation')
    def interfield(self):
        class Schema(deform.Schema):
            name = deform.SchemaNode(
                deform.String(),
                description='Content name')
            title = deform.SchemaNode(
                deform.String(),
                description='Content title (must start with content name)')
        def validator(form, value):
            if not value['title'].startswith(value['name']):
                exc = colander.Invalid(form, 'Title must start with name')
                exc['title'] = 'Must start with name %s' % value['name']
                raise exc
        schema = Schema(validator=validator)
        form = deform.Form(schema, buttons=('submit',))
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='fielddefaults')
    @demonstrate('Field Defaults')
    def fielddefaults(self):
        class Schema(deform.Schema):
            artist = deform.SchemaNode(
                deform.String(),
                default = 'Grandaddy',
                description='Song name')
            album = deform.SchemaNode(
                deform.String(),
                default='Just Like the Fambly Cat')
            song = deform.SchemaNode(
                deform.String(),
                description='Song name')
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='unicodeeverywhere')
    @demonstrate('Unicode Everywhere')
    def unicodeeverywhere(self):
        class Schema(deform.Schema):
            field = deform.SchemaNode(
                deform.String(),
                title = u'По оживлённым берегам',
                description=(u"子曰：「學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？ "
                             u"人不知而不慍，不亦君子乎？」"),
                default=u'☃',
                )
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='select')
    @demonstrate('Select Widget')
    def select(self):
        choices = (
            ('', '- Select -'),
            ('habanero', 'Habanero'),
            ('jalapeno', 'Jalapeno'),
            ('chipotle', 'Chipotle')
            )
        class Schema(deform.Schema):
            pepper = deform.SchemaNode(
                deform.String(),
                )
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['pepper'].widget = deform.widget.SelectWidget(
            values=choices)
        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='checkboxchoice')
    @demonstrate('Checkbox Choice Widget')
    def checkboxchoice(self):
        choices = (('habanero', 'Habanero'), ('jalapeno', 'Jalapeno'),
                   ('chipotle', 'Chipotle'))
        class Schema(deform.Schema):
            pepper = deform.SchemaNode(
                deform.Set(),
                )
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['pepper'].widget = deform.widget.CheckboxChoiceWidget(
            values=choices)
        return self.render_form(form)

    @bfg_view(renderer='templates/translated_form.pt', name='i18n')
    @demonstrate('Internationalization')
    def i18n(self):
        minmax = {'min':1, 'max':10}
        locale_name = get_locale_name(self.request)
        class Schema(deform.Schema):
            
            number = deform.SchemaNode(
                colander.Integer(),
                title=_('A number between ${min} and ${max}',
                        mapping=minmax),
                description=_('A number between ${min} and ${max}',
                              mapping=minmax),
                validator = colander.Range(1, 10),
                )
            _LOCALE_ = deform.SchemaNode(deform.String(),
                                         default=locale_name)

        schema = Schema()
        form = deform.Form(
            schema,
            buttons=[deform.Button('submit', _('Submit'))],
            )

        form['_LOCALE_'].widget = deform.widget.HiddenWidget()

        return self.render_form(form)

    @bfg_view(renderer='templates/form.pt', name='hidden_field')
    @demonstrate('Hidden Field Widget')
    def hidden_field(self):
        class Schema(deform.Schema):
            sneaky = deform.SchemaNode(
                deform.Boolean(),
                default=True,
                )
        schema = Schema()
        form = deform.Form(schema, buttons=('submit',))
        form['sneaky'].widget = deform.widget.HiddenWidget()
        return self.render_form(form)

class MemoryTmpStore(dict):
    def preview_url(self, uid):
        return None

tmpstore = MemoryTmpStore()

def run(global_config, **settings):
    settings['debug_templates'] = 'true'
    config = Configurator(package=deform.demo, settings=settings)
    config.begin()
    config.add_static_view('static', 'deform:static')
    config.add_translation_dirs(
        'colander:locale',
        'deform:locale',
        'deform.demo:locale'
        )
    config.scan()
    config.end()
    return config.make_wsgi_app()
