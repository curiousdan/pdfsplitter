### Table of Contents

  * QSpinBox
    * Synopsis
      * Functions
      * Virtual functions
      * Slots
      * Signals
    * Detailed Description
      * Subclassing QSpinBox
        * `PySide2.QtWidgets.QSpinBox`
          * `PySide2.QtWidgets.QSpinBox.cleanText()`
          * `PySide2.QtWidgets.QSpinBox.displayIntegerBase()`
          * `PySide2.QtWidgets.QSpinBox.maximum()`
          * `PySide2.QtWidgets.QSpinBox.minimum()`
          * `PySide2.QtWidgets.QSpinBox.prefix()`
          * `PySide2.QtWidgets.QSpinBox.setDisplayIntegerBase()`
          * `PySide2.QtWidgets.QSpinBox.setMaximum()`
          * `PySide2.QtWidgets.QSpinBox.setMinimum()`
          * `PySide2.QtWidgets.QSpinBox.setPrefix()`
          * `PySide2.QtWidgets.QSpinBox.setRange()`
          * `PySide2.QtWidgets.QSpinBox.setSingleStep()`
          * `PySide2.QtWidgets.QSpinBox.setStepType()`
          * `PySide2.QtWidgets.QSpinBox.setSuffix()`
          * `PySide2.QtWidgets.QSpinBox.setValue()`
          * `PySide2.QtWidgets.QSpinBox.singleStep()`
          * `PySide2.QtWidgets.QSpinBox.stepType()`
          * `PySide2.QtWidgets.QSpinBox.suffix()`
          * `PySide2.QtWidgets.QSpinBox.textChanged()`
          * `PySide2.QtWidgets.QSpinBox.textFromValue()`
          * `PySide2.QtWidgets.QSpinBox.value()`
          * `PySide2.QtWidgets.QSpinBox.valueChanged()`
          * `PySide2.QtWidgets.QSpinBox.valueFromText()`

#### Previous topic

QSpacerItem

#### Next topic

QSplashScreen

### Quick search

# QSpinBox¶

> The `QSpinBox` class provides a spin box widget. More…

## Synopsis¶

### Functions¶

  * def `cleanText` ()

  * def `displayIntegerBase` ()

  * def `maximum` ()

  * def `minimum` ()

  * def `prefix` ()

  * def `setDisplayIntegerBase` (base)

  * def `setMaximum` (max)

  * def `setMinimum` (min)

  * def `setPrefix` (prefix)

  * def `setRange` (min, max)

  * def `setSingleStep` (val)

  * def `setStepType` (stepType)

  * def `setSuffix` (suffix)

  * def `singleStep` ()

  * def `stepType` ()

  * def `suffix` ()

  * def `value` ()

### Virtual functions¶

  * def `textFromValue` (val)

  * def `valueFromText` (text)

### Slots¶

  * def `setValue` (val)

### Signals¶

  * def `textChanged` (arg__1)

  * def `valueChanged` (arg__1)

  * def `valueChanged` (arg__1)

## Detailed Description¶

> `QSpinBox` is designed to handle integers and discrete sets of values (e.g., month names); use `QDoubleSpinBox` for floating point values.
>
> `QSpinBox` allows the user to choose a value by clicking the up/down buttons or pressing up/down on the keyboard to increase/decrease the value currently displayed. The user can also type the value in manually. The spin box supports integer values but can be extended to use different strings with `validate()` , `textFromValue()` and `valueFromText()` .
>
> Every time the value changes `QSpinBox` emits `valueChanged()` and `textChanged()` signals, the former providing a int and the latter a `QString` . The `textChanged()` signal provides the value with both `prefix()` and `suffix()` . The current value can be fetched with `value()` and set with `setValue()` .
>
> Clicking the up/down buttons or using the keyboard accelerator’s up and down arrows will increase or decrease the current value in steps of size `singleStep()` . If you want to change this behaviour you can reimplement the virtual function `stepBy()` . The minimum and maximum value and the step size can be set using one of the constructors, and can be changed later with `setMinimum()` , `setMaximum()` and `setSingleStep()` .
>
> Most spin boxes are directional, but `QSpinBox` can also operate as a circular spin box, i.e. if the range is 0-99 and the current value is 99, clicking “up” will give 0 if `wrapping()` is set to true. Use `setWrapping()` if you want circular behavior.
>
> The displayed value can be prepended and appended with arbitrary strings indicating, for example, currency or the unit of measurement. See `setPrefix()` and `setSuffix()` . The text in the spin box is retrieved with `text()` (which includes any `prefix()` and `suffix()` ), or with `cleanText()` (which has no `prefix()` , no `suffix()` and no leading or trailing whitespace).
>
> It is often desirable to give the user a special (often default) choice in addition to the range of numeric values. See `setSpecialValueText()` for how to do this with `QSpinBox` .

### Subclassing QSpinBox¶

> If using `prefix()` , `suffix()` , and `specialValueText()` don’t provide enough control, you subclass `QSpinBox` and reimplement `valueFromText()` and `textFromValue()` . For example, here’s the code for a custom spin box that allows the user to enter icon sizes (e.g., “32 x 32”):
```
>     def valueFromText(self, text):
>         regExp = QRegExp(tr("(\\d+)(\\s*[xx]\\s*\\d+)?"))
>  
>         if regExp.exactMatch(text):
>             return regExp.cap(1).toInt()
>         else:
>             return 0
>  
>     def textFromValue(self, value):
>         return self.tr("%1 x %1").arg(value)
>  
```

>
> See the Icons example for the full source code.
>
> See also
>
> `QDoubleSpinBox` `QDateTimeEdit` `QSlider` Spin Boxes Example

_class _PySide2.QtWidgets.QSpinBox([_parent=None_])¶

    

> param parent:
>  
>
> `PySide2.QtWidgets.QWidget`

Constructs a spin box with 0 as minimum value and 99 as maximum value, a step value of 1. The value is initially set to 0. It is parented to `parent` .

See also

`setMinimum()` `setMaximum()` `setSingleStep()`

PySide2.QtWidgets.QSpinBox.cleanText()¶

    

Return type:

    

str

This property holds the text of the spin box excluding any prefix, suffix, or leading or trailing whitespace..

See also

`text` `prefix` `suffix`

PySide2.QtWidgets.QSpinBox.displayIntegerBase()¶

    

Return type:

    

int

This property holds the base used to display the value of the spin box.

The default value is 10.

See also

`textFromValue()` `valueFromText()`

PySide2.QtWidgets.QSpinBox.maximum()¶

    

Return type:

    

int

This property holds the maximum value of the spin box.

When setting this property the minimum is adjusted if necessary, to ensure that the range remains valid.

The default maximum value is 99.

See also

`setRange()` `specialValueText`

PySide2.QtWidgets.QSpinBox.minimum()¶

    

Return type:

    

int

This property holds the minimum value of the spin box.

When setting this property the `maximum` is adjusted if necessary to ensure that the range remains valid.

The default minimum value is 0.

See also

`setRange()` `specialValueText`

PySide2.QtWidgets.QSpinBox.prefix()¶

    

Return type:

    

str

This property holds the spin box’s prefix.

The prefix is prepended to the start of the displayed value. Typical use is to display a unit of measurement or a currency symbol. For example:

```
sb.setPrefix("$")

```

To turn off the prefix display, set this property to an empty string. The default is no prefix. The prefix is not displayed when `value()` == `minimum()` and `specialValueText()` is set.

If no prefix is set, returns an empty string.

See also

`suffix()` `setSuffix()` `specialValueText()` `setSpecialValueText()`

PySide2.QtWidgets.QSpinBox.setDisplayIntegerBase(_base_)¶

    

Parameters:

    

**base** – int

This property holds the base used to display the value of the spin box.

The default value is 10.

See also

`textFromValue()` `valueFromText()`

PySide2.QtWidgets.QSpinBox.setMaximum(_max_)¶

    

Parameters:

    

**max** – int

This property holds the maximum value of the spin box.

When setting this property the minimum is adjusted if necessary, to ensure that the range remains valid.

The default maximum value is 99.

See also

`setRange()` `specialValueText`

PySide2.QtWidgets.QSpinBox.setMinimum(_min_)¶

    

Parameters:

    

**min** – int

This property holds the minimum value of the spin box.

When setting this property the `maximum` is adjusted if necessary to ensure that the range remains valid.

The default minimum value is 0.

See also

`setRange()` `specialValueText`

PySide2.QtWidgets.QSpinBox.setPrefix(_prefix_)¶

    

Parameters:

    

**prefix** – str

This property holds the spin box’s prefix.

The prefix is prepended to the start of the displayed value. Typical use is to display a unit of measurement or a currency symbol. For example:

```
sb.setPrefix("$")

```

To turn off the prefix display, set this property to an empty string. The default is no prefix. The prefix is not displayed when `value()` == `minimum()` and `specialValueText()` is set.

If no prefix is set, returns an empty string.

See also

`suffix()` `setSuffix()` `specialValueText()` `setSpecialValueText()`

PySide2.QtWidgets.QSpinBox.setRange(_min_ , _max_)¶

    

Parameters:

    

  * **min** – int

  * **max** – int

Convenience function to set the `minimum` , and `maximum` values with a single function call.

```
setRange(minimum, maximum)

```

is equivalent to:

```
setMinimum(minimum)
setMaximum(maximum)

```

See also

`minimum` `maximum`

PySide2.QtWidgets.QSpinBox.setSingleStep(_val_)¶

    

Parameters:

    

**val** – int

This property holds the step value.

When the user uses the arrows to change the spin box’s value the value will be incremented/decremented by the amount of the . The default value is 1. Setting a value of less than 0 does nothing.

PySide2.QtWidgets.QSpinBox.setStepType(_stepType_)¶

    

Parameters:

    

**stepType** – `StepType`

This property holds The step type..

The step type can be single step or adaptive decimal step.

PySide2.QtWidgets.QSpinBox.setSuffix(_suffix_)¶

    

Parameters:

    

**suffix** – str

This property holds the suffix of the spin box.

The suffix is appended to the end of the displayed value. Typical use is to display a unit of measurement or a currency symbol. For example:

```
sb.setSuffix(" km")

```

To turn off the suffix display, set this property to an empty string. The default is no suffix. The suffix is not displayed for the `minimum()` if `specialValueText()` is set.

If no suffix is set, returns an empty string.

See also

`prefix()` `setPrefix()` `specialValueText()` `setSpecialValueText()`

PySide2.QtWidgets.QSpinBox.setValue(_val_)¶

    

Parameters:

    

**val** – int

This property holds the value of the spin box.

will emit `valueChanged()` if the new value is different from the old one. The value property has a second notifier signal which includes the spin box’s prefix and suffix.

PySide2.QtWidgets.QSpinBox.singleStep()¶

    

Return type:

    

int

This property holds the step value.

When the user uses the arrows to change the spin box’s value the value will be incremented/decremented by the amount of the . The default value is 1. Setting a value of less than 0 does nothing.

PySide2.QtWidgets.QSpinBox.stepType()¶

    

Return type:

    

`StepType`

This property holds The step type..

The step type can be single step or adaptive decimal step.

PySide2.QtWidgets.QSpinBox.suffix()¶

    

Return type:

    

str

This property holds the suffix of the spin box.

The suffix is appended to the end of the displayed value. Typical use is to display a unit of measurement or a currency symbol. For example:

```
sb.setSuffix(" km")

```

To turn off the suffix display, set this property to an empty string. The default is no suffix. The suffix is not displayed for the `minimum()` if `specialValueText()` is set.

If no suffix is set, returns an empty string.

See also

`prefix()` `setPrefix()` `specialValueText()` `setSpecialValueText()`

PySide2.QtWidgets.QSpinBox.textChanged(_arg__1_)¶

    

Parameters:

    

**arg__1** – str

PySide2.QtWidgets.QSpinBox.textFromValue(_val_)¶

    

Parameters:

    

**val** – int

Return type:

    

str

This virtual function is used by the spin box whenever it needs to display the given `value` . The default implementation returns a string containing `value` printed in the standard way using `locale()` .toString(), but with the thousand separator removed unless `setGroupSeparatorShown()` is set. Reimplementations may return anything. (See the example in the detailed description.)

Note: `QSpinBox` does not call this function for `specialValueText()` and that neither `prefix()` nor `suffix()` should be included in the return value.

If you reimplement this, you may also need to reimplement `valueFromText()` and `validate()`

See also

`valueFromText()` `validate()` `groupSeparator()`

PySide2.QtWidgets.QSpinBox.value()¶

    

Return type:

    

int

This property holds the value of the spin box.

will emit `valueChanged()` if the new value is different from the old one. The value property has a second notifier signal which includes the spin box’s prefix and suffix.

PySide2.QtWidgets.QSpinBox.valueChanged(_arg__1_)¶

    

Parameters:

    

**arg__1** – str

Note

This function is deprecated.

```
def callback_unicode(value_as_unicode):
    print 'unicode value changed:', repr(value_as_unicode)

app = QApplication(sys.argv)
spinbox = QSpinBox()
spinbox.valueChanged[unicode].connect(callback_unicode)
spinbox.show()
sys.exit(app.exec_())

```

PySide2.QtWidgets.QSpinBox.valueChanged(_arg__1_)

    

Parameters:

    

**arg__1** – int

```
def callback_int(value_as_int):
    print 'int value changed:', repr(value_as_int)

app = QApplication(sys.argv)
spinbox = QSpinBox()
spinbox.valueChanged[unicode].connect(callback_unicode)
spinbox.show()
sys.exit(app.exec_())

```

PySide2.QtWidgets.QSpinBox.valueFromText(_text_)¶

    

Parameters:

    

**text** – str

Return type:

    

int

This virtual function is used by the spin box whenever it needs to interpret `text` entered by the user as a value.

Subclasses that need to display spin box values in a non-numeric way need to reimplement this function.

Note: `QSpinBox` handles `specialValueText()` separately; this function is only concerned with the other values.

See also

`textFromValue()` `validate()`
