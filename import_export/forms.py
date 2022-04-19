import os.path
from typing import Dict, List, Tuple

from django import forms
from django.contrib.admin.helpers import ActionForm
from django.utils.translation import gettext_lazy as _
from import_export.fields import Field
from import_export.resources import Resource


class ImportForm(forms.Form):
    import_file = forms.FileField(
        label=_('File to import')
        )
    input_format = forms.ChoiceField(
        label=_('Format'),
        choices=(),
        )

    def __init__(self, import_formats, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []
        for i, f in enumerate(import_formats):
            choices.append((str(i), f().get_title(),))
        if len(import_formats) > 1:
            choices.insert(0, ('', '---'))

        self.fields['input_format'].choices = choices


class ConfirmImportForm(forms.Form):
    import_file_name = forms.CharField(widget=forms.HiddenInput())
    original_file_name = forms.CharField(widget=forms.HiddenInput())
    input_format = forms.CharField(widget=forms.HiddenInput())

    def clean_import_file_name(self):
        data = self.cleaned_data['import_file_name']
        data = os.path.basename(data)
        return data


class ExportForm(forms.Form):
    is_large_export = forms.BooleanField(label="Large data export", required=False)
        
    file_format = forms.ChoiceField(
        label=_('Format'),
        choices=(),
        )
    
    def _get_select_format_name(self, value):
        file_format = dict(self.fields["file_format"].choices)
        return file_format.get(value, "")
    
    
    def _create_resource_fields(self, resource_instance: Resource):

        resource_fields: List[Field] = resource_instance.fields
        export_order: Tuple[str] = resource_instance.get_export_order()

        for field in export_order:
            field_name = f"resource_{field}"
            self.fields[field_name] = forms.BooleanField(label=f"{resource_fields[field].column_name}", required=False, initial=True)
    
    def __init__(self, formats, *args, **kwargs):
        resource_instance = kwargs.pop("resource_instance", None)

        super().__init__(*args, **kwargs)
        choices = [] 
        
        for i, f in enumerate(formats):
            choices.append((str(i), f().get_title(),))
        if len(formats) > 1:
            choices.insert(0, ('', '---'))

        self.fields['file_format'].choices = choices
        self._create_resource_fields(resource_instance)
    
    def get_selected_fields(self) -> Dict[str,bool]:
        cleaned_data = super().clean() 
        result = {}
        
        for field_name in self.fields.keys():
            if "resource_" in field_name:
                 result[field_name.replace("resource_","")] = cleaned_data.get(field_name, True)
                 
        return result
    
    def clean(self):
        cleaned_data = super().clean() 
        file_format = self._get_select_format_name(cleaned_data['file_format'])
        is_large_export = cleaned_data.get("is_large_export", False)

        if is_large_export and file_format != "csv":
            self.add_error("is_large_export", "큰 데이터 내보내기는 csv 확장자만 이용이 가능합니다.") 

        return cleaned_data
    

def export_action_form_factory(formats):
    """
    Returns an ActionForm subclass containing a ChoiceField populated with
    the given formats.
    """
    class _ExportActionForm(ActionForm):
        """
        Action form with export format ChoiceField.
        """
        file_format = forms.ChoiceField(
            label=_('Format'), choices=formats, required=False)
    _ExportActionForm.__name__ = str('ExportActionForm')

    return _ExportActionForm
