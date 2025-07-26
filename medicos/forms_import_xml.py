from django import forms

class NotaFiscalImportXMLForm(forms.Form):
    xml_file = forms.FileField(
        label='Selecione um arquivo XML de Nota Fiscal',
        help_text='Importe um arquivo XML de NF-e ou NFS-e.',
        required=True
    )
