import {AfterViewInit, ChangeDetectorRef, Component} from '@angular/core';
import {FieldType} from '@ngx-formly/core';
import {TranslateService} from '@ngx-translate/core';

@Component({
    selector: 'grm-input-custom',
    templateUrl: './input-custom.component.html',
    styleUrls: ['./input-custom.component.scss']
})
export class InputCustomComponent extends FieldType implements AfterViewInit {

    constructor(
        public translate: TranslateService,
        private cdr: ChangeDetectorRef
    ) {
        super();
    }

    ngAfterViewInit(): void {
        this.initControl();
    }

    initControl() {
        const fieldKey = this.field.key as string;
        if (this.form.controls[fieldKey].value) {
            this.form.controls[fieldKey].setValue(this.validateValue({target: {value: this.form.controls[fieldKey].value}}));
            this.cdr.detectChanges();
        }
    }

    validateValue(event: any) {
        const value = event.target.value;

        if (this.isValidInput(value)) {
            this.to.value = value;
            this.formControl.setValue(value);
        }

        return value;
    }

    isValidInput(value: any) {
        if (!(typeof value === 'string' || value instanceof String)) {
            value = '' + value;
        }
        this.setFieldValid();

        if (value !== undefined && value !== null && this.to.type === 'number') {
            if (((this.to.min !== undefined && this.to.min || (this.to.max !== undefined)))) {
                this.to.value = '';
                this.formControl.setValue('');
                this.setFieldInvalid();
                return false;
            }

            const dots = ((value || '').match(/\./g) || []).length;
            const commas = ((value || '').match(/,/g) || []).length;

            if ((dots === 0 && commas === 0) || (dots === 1 && commas === 0)) {
                return true;
            }

            if (commas === 1 && dots === 0) {
                return true;
            }

            if (commas === 0 && dots > 1) {
                this.setFieldInvalid();
                return false;
            }

            if (dots === 0 && commas > 1) {
                this.setFieldInvalid();
                return false;
            }

            if (commas > 1 && dots > 1) {
                this.setFieldInvalid();
                return false;
            }
        }

        return true;
    }

    setFieldInvalid() {
        const fieldKey = this.field.key as string;
        this.form.controls[fieldKey].setErrors({'incorrect': true});
    }

    setFieldValid() {
        const fieldKey = this.field.key as string;
        this.form.controls[fieldKey].setErrors({'incorrect': false});
    }

    checkKey(event: any) {
        if (this.to.type !== undefined && this.to.type === 'number') {
            if (event.key === ',' || event.key === '.') {
                return;
            }
            if (isNaN(event.key) || event.key === ' ' || event.key === '') {
                event.returnValue = '';
            }
        }
    }

    formatNumber(event: any) {
        if (this.to.type !== undefined && this.to.type !== 'number') {
            return;
        }

        this.setFieldValid();
        let text = event.target.value;
        if (text !== '' && this.isValidInput(text)) {
            text = this.prepareForFormat(text);
            this.to.value = text;
            this.formControl.setValue(text);
        }
        return text;
    }

    prepareForFormat(text: any) {

        if (!(typeof text === 'string' || text instanceof String)) {
            text = '' + text;
        }

        const dots = ((text || '').match(/\./g) || []).length;
        const commas = ((text || '').match(/,/g) || []).length;

        if ((dots === 0 && commas === 0) || (dots === 1 && commas === 0)) {
            return text;
        }

        if (commas === 1 && dots === 0) {
            return text.replace(',', '.');
        }

        if (commas === 1 && dots > 1) {
            return text.replace(/\./g, '').replace(',', '.');
        }

        if (dots === 1 && commas > 1) {
            return text.replace(',', '');
        }

        if (dots === 1 && commas === 1) {
            const commaIndex = text.indexOf(',');
            const dotIndex = text.indexOf('.');
            if (commaIndex > dotIndex) {
                return text.replace(/\./g, '').replace(',', '.');
            } else {
                return text.replace(',', '');
            }
        }

        return text;
    }
}
