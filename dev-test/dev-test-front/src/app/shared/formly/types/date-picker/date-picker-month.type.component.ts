import { Component, OnInit } from '@angular/core';
import { FieldType } from '@ngx-formly/core';
import { locales } from './date-picker.locales';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'grm-date-picker-month',
  templateUrl: './date-picker-month.type.component.html',
  styleUrls: ['./date-picker.type.component.scss']
})
export class FormlyFieldDateMonthPickerComponent extends FieldType implements OnInit {

  locale = 'pt-br';
  selectionMode: 'single';
  locales = locales;

  constructor(private translateService: TranslateService) {
    super();
  }

  ngOnInit() {
    if (this.to.selectionMode) {
      this.selectionMode = this.to.selectionMode;
    }

    if (this.translateService.currentLang) {
      this.locale = this.translateService.currentLang;
    }
  }

}
