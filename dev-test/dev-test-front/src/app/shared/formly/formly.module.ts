import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgSelectModule } from '@ng-select/ng-select';
import { InputSwitchModule } from 'primeng/inputswitch';
import { NgOptionHighlightModule } from '@ng-select/ng-option-highlight';
import { FormlyModule } from '@ngx-formly/core';
import { FormlyBootstrapModule } from '@ngx-formly/bootstrap';
import { FormlyFieldSelectComponent } from './types/select/select.type.component';
import { FormlyFieldDatePickerComponent } from './types/date-picker/date-picker.type.component';
import { FormlyFieldSwitchComponent } from './types/switch/switch.component';
import { AccordionModule } from 'primeng/accordion';
import { InputMaskModule } from 'primeng/inputmask';

import { CalendarModule } from 'primeng/calendar';
import { EditorModule } from 'primeng/editor';
import { HorizontalWrapperComponent } from './horizontal-wrapper/horizontal-wrapper.component';
import { InputMaskComponent } from './types/input-mask/input-mask.component';
import { ColorPickerModule, InputNumberModule } from 'primeng';
import { FormlyFieldDateMonthPickerComponent } from './types/date-picker/date-picker-month.type.component';
import { InputFileComponent } from './types/input-file/input-file.component';
import { InputFileValueAccessor } from './types/input-file/input-file-value-acessor';
import { ColorPickerComponent } from './types/color-picker/color-picker.component';
import { InputCustomComponent } from './types/input-custom/input-custom.component';
import { InputNumberNewComponent } from './types/input-number-new/input-number-new.component';
import { TranslateModule } from '@ngx-translate/core';

@NgModule({
  imports: [
    ColorPickerModule,
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    NgSelectModule,
    InputSwitchModule,
    CalendarModule,
    EditorModule,
    NgOptionHighlightModule,
    FormlyBootstrapModule,
    AccordionModule,
    InputMaskModule,
    InputNumberModule,
    TranslateModule,
    FormlyModule.forRoot({
      wrappers: [{ name: 'form-field-horizontal', component: HorizontalWrapperComponent }],
      types: [
        { name: 'lup-select', component: FormlyFieldSelectComponent },
        { name: 'lup-date-picker', component: FormlyFieldDatePickerComponent },
        { name: 'lup-date-picker-month', component: FormlyFieldDateMonthPickerComponent },
        { name: 'lup-switch', component: FormlyFieldSwitchComponent },
        { name: 'lup-input-mask', component: InputMaskComponent },
        { name: 'lup-input-file', component: InputFileComponent },
        { name: 'lup-color-picker', component: ColorPickerComponent },
        { name: 'lup-input-custom', component: InputCustomComponent },
        { name: 'lup-input-number-new', component: InputNumberNewComponent }
      ]
    }),
  ],
    exports: [FormsModule, FormlyModule, ReactiveFormsModule, NgSelectModule, NgOptionHighlightModule, FormlyFieldSwitchComponent, ColorPickerModule, TranslateModule],
  declarations: [FormlyFieldSelectComponent, FormlyFieldDatePickerComponent, FormlyFieldDateMonthPickerComponent, FormlyFieldSwitchComponent, HorizontalWrapperComponent, InputMaskComponent, InputFileComponent, InputFileValueAccessor, ColorPickerComponent, InputCustomComponent, InputNumberNewComponent]
})
export class GRMFormlyModule { }
