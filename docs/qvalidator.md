### Table of Contents

  * QValidator
    * Synopsis
      * Functions
      * Virtual functions
      * Signals
    * Detailed Description
      * `PySide2.QtGui.QValidator`
        * `PySide2.QtGui.QValidator.State`
        * `PySide2.QtGui.QValidator.changed()`
        * `PySide2.QtGui.QValidator.fixup()`
        * `PySide2.QtGui.QValidator.locale()`
        * `PySide2.QtGui.QValidator.setLocale()`
        * `PySide2.QtGui.QValidator.validate()`

#### Previous topic

QTransform

#### Next topic

QVector2D

### Quick search

# QValidator¶

> The `QValidator` class provides validation of input text. More…

**Inherited by:** QDoubleValidator, QIntValidator, QRegExpValidator, QRegularExpressionValidator

## Synopsis¶

### Functions¶

  * def `locale` ()

  * def `setLocale` (locale)

### Virtual functions¶

  * def `fixup` (arg__1)

  * def `validate` (arg__1, arg__2)

### Signals¶

  * def `changed` ()

## Detailed Description¶

> The class itself is abstract. Two subclasses, `QIntValidator` and `QDoubleValidator` , provide basic numeric-range checking, and `QRegExpValidator` provides general checking using a custom regular expression.
>
> If the built-in validators aren’t sufficient, you can subclass `QValidator` . The class has two virtual functions: `validate()` and `fixup()` .
>
> `validate()` must be implemented by every subclass. It returns `Invalid` , `Intermediate` or `Acceptable` depending on whether its argument is valid (for the subclass’s definition of valid).
>
> These three states require some explanation. An `Invalid` string is _clearly_ invalid. `Intermediate` is less obvious: the concept of validity is difficult to apply when the string is incomplete (still being edited). `QValidator` defines `Intermediate` as the property of a string that is neither clearly invalid nor acceptable as a final result. `Acceptable` means that the string is acceptable as a final result. One might say that any string that is a plausible intermediate state during entry of an `Acceptable` string is `Intermediate` .
>
> Here are some examples:
>
>   * For a line edit that accepts integers from 10 to 1000 inclusive, 42 and 123 are `Acceptable` , the empty string, 5, or 1234 are `Intermediate` , and “asdf” and 10114 is `Invalid` .
>
>   * For an editable combobox that accepts URLs, any well-formed URL is `Acceptable` , “http://example.com/,” is `Intermediate` (it might be a cut and paste action that accidentally took in a comma at the end), the empty string is `Intermediate` (the user might select and delete all of the text in preparation for entering a new URL) and “http:///./” is `Invalid` .
>
>   * For a spin box that accepts lengths, “11cm” and “1in” are `Acceptable` , “11” and the empty string are `Intermediate` , and “http://example.com” and “hour” are `Invalid` .
>
>

>
> `fixup()` is provided for validators that can repair some user errors. The default implementation does nothing. `QLineEdit` , for example, will call `fixup()` if the user presses Enter (or Return) and the content is not currently valid. This allows the `fixup()` function the opportunity of performing some magic to make an `Invalid` string `Acceptable` .
>
> A validator has a locale, set with `setLocale()` . It is typically used to parse localized data. For example, `QIntValidator` and `QDoubleValidator` use it to parse localized representations of integers and doubles.
>
> `QValidator` is typically used with `QLineEdit` , `QSpinBox` and `QComboBox` .
>
> See also
>
> `QIntValidator` `QDoubleValidator` `QRegExpValidator` Line Edits Example

_class _PySide2.QtGui.QValidator([_parent=None_])¶

    

> param parent:
>  
>
> `PySide2.QtCore.QObject`

Sets up the validator. The `parent` parameter is passed on to the `QObject` constructor.

PySide2.QtGui.QValidator.State¶

    

This enum type defines the states in which a validated string can exist.

Constant | Description  
---|---  
QValidator.Invalid | The string is _clearly_ invalid.  
QValidator.Intermediate | The string is a plausible intermediate value.  
QValidator.Acceptable | The string is acceptable as a final result; i.e. it is valid.  
  
PySide2.QtGui.QValidator.changed()¶

    

PySide2.QtGui.QValidator.fixup(_arg__1_)¶

    

Parameters:

    

**arg__1** – str

This function attempts to change `input` to be valid according to this validator’s rules. It need not result in a valid string: callers of this function must re-test afterwards; the default does nothing.

Reimplementations of this function can change `input` even if they do not produce a valid string. For example, an ISBN validator might want to delete every character except digits and “-”, even if the result is still not a valid ISBN; a surname validator might want to remove whitespace from the start and end of the string, even if the resulting string is not in the list of accepted surnames.

PySide2.QtGui.QValidator.locale()¶

    

Return type:

    

`PySide2.QtCore.QLocale`

Returns the locale for the validator. The locale is by default initialized to the same as QLocale().

See also

`setLocale()` `QLocale()`

PySide2.QtGui.QValidator.setLocale(_locale_)¶

    

Parameters:

    

**locale** – `PySide2.QtCore.QLocale`

Sets the `locale` that will be used for the validator. Unless has been called, the validator will use the default locale set with `setDefault()` . If a default locale has not been set, it is the operating system’s locale.

See also

`locale()` `setDefault()`

PySide2.QtGui.QValidator.validate(_arg__1_ , _arg__2_)¶

    

Parameters:

    

  * **arg__1** – str

  * **arg__2** – int

Return type:

    

PyObject

This virtual function returns `Invalid` if `input` is invalid according to this validator’s rules, `Intermediate` if it is likely that a little more editing will make the input acceptable (e.g. the user types “4” into a widget which accepts integers between 10 and 99), and `Acceptable` if the input is valid.

The function can change both `input` and `pos` (the cursor position) if required.
