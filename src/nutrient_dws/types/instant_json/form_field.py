from typing import Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.instant_json.actions import Action


class BaseFormField(TypedDict):
    v: Literal[1]
    id: NotRequired[str]
    name: str
    label: str
    annotationIds: list[str]
    pdfObjectId: NotRequired[int]
    flags: NotRequired[list[Literal["readOnly", "required", "noExport"]]]


class ButtonFormField(BaseFormField):
    type: Literal["pspdfkit/form-field/button"]
    buttonLabel: str


class FormFieldOption(TypedDict):
    label: str
    value: str


FormFieldOptions = list[FormFieldOption]


FormFieldDefaultValues = list[str]


class FormFieldAdditionalActionsEvent(TypedDict):
    onChange: NotRequired[Action]
    onCalculate: NotRequired[Action]


class ChoiceFormField(TypedDict):
    options: FormFieldOptions
    multiSelect: NotRequired[bool]
    commitOnChange: NotRequired[bool]
    defaultValues: NotRequired[FormFieldDefaultValues]
    additionalActions: NotRequired[FormFieldAdditionalActionsEvent]


class FormFieldAdditionalActionsInput(TypedDict):
    onInput: NotRequired[Action]
    onFormat: NotRequired[Action]


class AdditionalActions(
    FormFieldAdditionalActionsEvent, FormFieldAdditionalActionsInput
):
    pass


class ListBoxFormField(BaseFormField):
    type: NotRequired[Literal["pspdfkit/form-field/listbox"]]
    additionalActions: NotRequired[AdditionalActions]
    options: FormFieldOptions
    multiSelect: NotRequired[bool]
    commitOnChange: NotRequired[bool]
    defaultValues: NotRequired[FormFieldDefaultValues]


class ComboBoxFormField(BaseFormField, ChoiceFormField):
    type: NotRequired[Literal["pspdfkit/form-field/combobox"]]
    edit: bool
    doNotSpellCheck: bool


class CheckboxFormField(BaseFormField):
    type: Literal["pspdfkit/form-field/checkbox"]
    options: FormFieldOptions
    defaultValues: FormFieldDefaultValues
    additionalActions: NotRequired[FormFieldAdditionalActionsEvent]


FormFieldDefaultValue = str


class RadioButtonFormField(BaseFormField):
    type: Literal["pspdfkit/form-field/radio"]
    options: FormFieldOptions
    defaultValue: NotRequired[FormFieldDefaultValue]
    noToggleToOff: NotRequired[bool]
    radiosInUnison: NotRequired[bool]


class TextFormField(BaseFormField):
    type: Literal["pspdfkit/form-field/text"]
    password: NotRequired[bool]
    maxLength: NotRequired[int]
    doNotSpellCheck: bool
    doNotScroll: bool
    multiLine: bool
    comb: bool
    defaultValue: FormFieldDefaultValue
    richText: NotRequired[bool]
    richTextValue: NotRequired[str]
    additionalActions: NotRequired[AdditionalActions]


class SignatureFormField(BaseFormField):
    type: NotRequired[Literal["pspdfkit/form-field/signature"]]


FormField = Union[
    ButtonFormField,
    ListBoxFormField,
    ComboBoxFormField,
    CheckboxFormField,
    RadioButtonFormField,
    TextFormField,
    SignatureFormField,
]
