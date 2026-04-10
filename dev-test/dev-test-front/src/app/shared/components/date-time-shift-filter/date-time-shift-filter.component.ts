import { Component, OnInit, OnDestroy, Input } from '@angular/core';
import { FormGroup } from '@angular/forms';
import { FormlyFieldConfig } from '@ngx-formly/core';
import {Observable, of, Subscription} from 'rxjs';
import { Shift } from '../../../../shift-control/model/shift';
import { TranslateService } from '@ngx-translate/core';
import { ToastService } from '../../../services/toast.service';
import { ShiftService } from '../../../../shift-control/services/shift-service';
import { DateTimeShiftFilter } from './date-time-shift-filter';
import { I18nService } from '../../../services/i18n.service';

@Component({
    selector: 'grm-date-time-shift-filter',
    templateUrl: './date-time-shift-filter.component.html',
    styleUrls: ['./date-time-shift-filter.component.scss']
})
export class DateTimeShiftFilterComponent implements OnInit, OnDestroy {

    form = new FormGroup({});
    startFields: FormlyFieldConfig[] = [];
    endFields: FormlyFieldConfig[] = [];
    allShiftList: any[];

    cols: any[];
    isProcessing = false;
    subscription: Subscription;

    hourOptions = {
        'pt-BR': [
            { label: '00:00', value: 0 }, { label: '01:00', value: 1 }, { label: '02:00', value: 2 }, { label: '03:00', value: 3 },
            { label: '04:00', value: 4 }, { label: '05:00', value: 5 }, { label: '06:00', value: 6 }, { label: '07:00', value: 7 },
            { label: '08:00', value: 8 }, { label: '09:00', value: 9 }, { label: '10:00', value: 10 }, { label: '11:00', value: 11 },
            { label: '12:00', value: 12 }, { label: '13:00', value: 13 }, { label: '14:00', value: 14 }, { label: '15:00', value: 15 },
            { label: '16:00', value: 16 }, { label: '17:00', value: 17 }, { label: '18:00', value: 18 }, { label: '19:00', value: 19 },
            { label: '20:00', value: 20 }, { label: '21:00', value: 21 }, { label: '22:00', value: 22 }, { label: '23:00', value: 23 }
        ],
        'en-US': [
            { label: '00:00 AM', value: 0 }, { label: '01:00 AM', value: 1 }, { label: '02:00 AM', value: 2 }, { label: '03:00 AM', value: 3 },
            { label: '04:00 AM', value: 4 }, { label: '05:00 AM', value: 5 }, { label: '06:00 AM', value: 6 }, { label: '07:00 AM', value: 7 },
            { label: '08:00 AM', value: 8 }, { label: '09:00 AM', value: 9 }, { label: '10:00 AM', value: 10 }, { label: '11:00 AM', value: 11 },
            { label: '12:00 AM', value: 12 }, { label: '01:00 PM', value: 13 }, { label: '02:00 PM', value: 14 }, { label: '03:00 PM', value: 15 },
            { label: '04:00 PM', value: 16 }, { label: '05:00 PM', value: 17 }, { label: '06:00 PM', value: 18 }, { label: '07:00 PM', value: 19 },
            { label: '08:00 PM', value: 20 }, { label: '09:00 PM', value: 21 }, { label: '10:00 PM', value: 22 }, { label: '11:00 PM', value: 23 }
        ]
    };

    shiftHourOptions: any[];

    @Input()
    model: DateTimeShiftFilter;

    @Input()
    minBeginDate: Date;

    @Input()
    minEndDate: Date;

    @Input()
    filterShift: boolean;

    private static getTimeOption(shiftHour: number, currentLanguage: any): any {
        return { label: DateTimeShiftFilterComponent.formatHour(shiftHour, currentLanguage), value: shiftHour };
    }

    public static formatHour(shiftHour: number, currentLanguage: any) {
        if (shiftHour > 24) {
            shiftHour = shiftHour - 24;
        }

        let hours = Math.trunc(shiftHour);
        const originalHours = hours;
        const minutes = (shiftHour - hours) * 60;

        let result = '';

        if (hours > 12 && currentLanguage === 'en-US') {
            hours = hours - 12;
        }
        result += hours < 10 ? '0' + hours : hours;
        result += minutes < 10 ? ':0' + minutes : ':' + minutes;
        if (currentLanguage === 'en-US') {
            if (originalHours <= 12) {
                result += ' AM';
            } else {
                result += ' PM';
            }
        }

        return result;
    }

    private static getCurrentFullHour() {
        const currentDate = new Date();
        return currentDate.getHours() + 1;
    }

    public static getEnd(end: number) {
        return end >= 24 ? (end - 24) : end;
    }

    constructor(private translate: TranslateService,
                private toast: ToastService,
                private shiftService: ShiftService,
                private i18nService: I18nService) { }

    ngOnInit() {
        this.loadAllShiftsWithTimezone();
        this.iniSubscription();
        setTimeout(()=> {
            this.initForm();
            this.setValuesInForm();
        }, 500);
    }

    ngOnDestroy(): void {
        this.subscription.unsubscribe();
    }

    private getHourOptions() {
        return this.hourOptions[this.i18nService.getLanguage()];
    }

    private loadAllShiftsWithTimezone() {
        this.shiftService.getAllShiftsWithTimezone().subscribe(
            allShifts => {
                this.shiftService.upsertManyShiftsInCache(allShifts);
                this.allShiftList = allShifts;
            },
            err => {
                this.throwErrorMsg(err);
            }
        );
    }

    private initForm() {

        this.minBeginDate = this.minBeginDate || new Date('1900-01-01');
        this.minEndDate = this.minEndDate || new Date('1900-01-01');

        this.startFields = [];
        this.endFields = [];
        this.startFields.push(
            {
                className: 'col-md-4 custom-items',
                name: 'beginDate',
                key: 'beginDate',
                type: 'lup-date-picker',
                templateOptions: {
                    selectionMode: 'single',
                    label: this.translate.instant('dateTimeShiftFilter.beginDate'),
                    required: true,
                    readonlyInput: false,
                    appendTo: 'body',
                    minDate: this.minBeginDate,
                    horizontalTemplate: false,
                    ngModel: this.model,
                    change: (field: any) => {
                        setTimeout(() => {
                            this.onDateChange('begin');
                        }, 500);
                    }
                }
            }
        );
        if (this.filterShift) {
            this.startFields.push(
                {
                    className: 'col-md-5 custom-middle-item',
                    name: 'shiftBeginId',
                    key: 'shiftBeginId',
                    type: 'lup-select',
                    templateOptions: {
                        multiple: false,
                        label: this.translate.instant('dateTimeShiftFilter.shift'),
                        placeholder: this.translate.instant('dateTimeShiftFilter.shiftPlaceHolder'),
                        bindValue: 'id',
                        bindLabel: 'nameAndBegin',
                        required: false,
                        horizontalTemplate: false,
                        options$: this.shiftService.allShiftsFromCurrentShiftGroup$,
                        appendTo: 'body',
                        trackByFn: (item: Shift) => item.id,
                        change: (field: any) => {
                            setTimeout(() => {
                                this.onShiftChange(field.formControl.value, 'begin');
                            }, 500);
                        }
                    }
                }
            );
        }
        this.startFields.push(
            {
                className: 'col-md-3 custom-items',
                key: 'beginHour',
                type: 'lup-select',
                templateOptions: {
                    label: this.translate.instant('dateTimeShiftFilter.startHour'),
                    required: true,
                    selectionMode: 'single',
                    bindValue: 'value',
                    bindLabel: 'label',
                    options$: this.getTimeOptions(),
                    change: (field: any) => {
                        setTimeout(() => {
                            this.onHourChange('begin');
                        }, 500);
                    }
                }
            }
        );
        this.endFields.push(
            {
                className: 'col-md-4 custom-items',
                name: 'endDate',
                key: 'endDate',
                type: 'lup-date-picker',
                templateOptions: {
                    selectionMode: 'single',
                    label: this.translate.instant('dateTimeShiftFilter.endDate'),
                    required: true,
                    readonlyInput: false,
                    appendTo: 'body',
                    minDate: this.minEndDate,
                    horizontalTemplate: false,
                    ngModel: this.model,
                    change: (field: any) => {
                        setTimeout(() => {
                            this.onDateChange('end');
                        }, 500);
                    }
                }
            }
        );
        if (this.filterShift) {
            this.endFields.push(
                {
                    className: 'col-md-5 custom-middle-item',
                    name: 'shiftEndId',
                    key: 'shiftEndId',
                    type: 'lup-select',
                    templateOptions: {
                        multiple: false,
                        label: this.translate.instant('dateTimeShiftFilter.shift'),
                        placeholder: this.translate.instant('dateTimeShiftFilter.shiftPlaceHolder'),
                        bindValue: 'id',
                        bindLabel: 'nameAndEnd',
                        required: false,
                        horizontalTemplate: false,
                        options$: this.shiftService.allShiftsFromCurrentShiftGroup$,
                        appendTo: 'body',
                        trackByFn: (item: Shift) => item.id,
                        change: (field: any) => {
                            setTimeout(() => {
                                this.onShiftChange(field.formControl.value, 'end');
                            }, 500);
                        }
                    }
                }
            );
        }
        this.endFields.push(
            {
                className: 'col-md-3 custom-items',
                key: 'endHour',
                type: 'lup-select',
                templateOptions: {
                    label: this.translate.instant('dateTimeShiftFilter.endHour'),
                    required: true,
                    selectionMode: 'single',
                    bindValue: 'value',
                    bindLabel: 'label',
                    options$: this.getTimeOptions(),
                    change: (field: any) => {
                        setTimeout(() => {
                            this.onHourChange('end');
                        }, 500);
                    }
                }
            }
        );
    }

    private onShiftChange(value: any, field: string) {
        this.shiftHourOptions = [];
        let selectedHourValue: number;
        if ('begin' === field) {
            if (!value) {
                //this.form.controls.endDate.setValue(new Date());
                selectedHourValue = 0;
                this.form.controls.beginHour.setValue(selectedHourValue);
                this.form.controls.beginHour.enable();
            } else {
                //this.form.controls.endDate.setValue(new Date());
                const selectedShift = this.allShiftList.filter(item => item.id === value).shift();
                this.shiftHourOptions.push(DateTimeShiftFilterComponent.getTimeOption(selectedShift.begin, this.i18nService.getLanguage()));
                selectedHourValue = this.shiftHourOptions[0].value;
                this.form.controls.beginHour.setValue(selectedHourValue);
                this.form.controls.beginHour.disable();
            }
        } else {
            if (!value) {
                //this.form.controls.endDate.setValue(new Date());
                selectedHourValue = 0;
                this.form.controls.endHour.setValue(selectedHourValue);
                this.form.controls.endHour.enable();
            } else {
                //this.form.controls.endDate.setValue(new Date());
                const selectedShift = this.allShiftList.filter(item => item.id === value).shift();

                if (selectedShift && selectedShift.end && selectedShift.end > 23 && this.model.beginDate.getDay() === this.model.endDate.getDay())  {
                    this.form.controls.endDate.setValue(new Date(this.model.endDate.getTime() + 24*60*60*1000)); //add 1 hour
                }

                this.shiftHourOptions.push(DateTimeShiftFilterComponent.getTimeOption(DateTimeShiftFilterComponent.getEnd(selectedShift.end), this.i18nService.getLanguage()));
                selectedHourValue = this.shiftHourOptions[0].value;
                this.form.controls.endHour.setValue(selectedHourValue);
                this.form.controls.endHour.disable();
            }
        }
        this.setModelHour(selectedHourValue, field);
    }

    private onDateChange(field: string) {
        if ('begin' === field) {
            const selectedHourValue = this.form.controls.beginHour.value;
            const hours = Math.trunc(selectedHourValue);
            const minutes = (selectedHourValue - hours) * 60;
            this.model.beginDate.setHours(hours, minutes, 0)
        } else {
            const selectedHourValue = this.form.controls.endHour.value;
            const hours = Math.trunc(selectedHourValue);
            const minutes = (selectedHourValue - hours) * 60;
            this.model.endDate.setHours(hours, minutes, 0)
        }
    }

    private onHourChange(field: string) {
        let control;
        if ('begin' === field) {
            control = this.form.controls.beginHour;
        } else {
            control = this.form.controls.endHour;
        }

        this.setModelHour(control.value, field);
    }

    private setModelHour(selectedHourValue: number, field: string) {
        const hours = Math.trunc(selectedHourValue);
        const minutes = (selectedHourValue - hours) * 60;
        if ('begin' === field && this.model.beginDate) {
            this.model.beginDate.setHours(hours, minutes, 0);
        }

        if ('end' === field && this.model.endDate) {
            this.model.endDate.setHours(hours, minutes, 0);
        }
    }

    private setValuesInForm() {
        setTimeout(() => {
            this.form.controls.beginDate.setValue(this.model.beginDate ? this.model.beginDate : null);
            this.form.controls.beginHour.setValue(0);
            this.setModelHour(0, 'begin');
            this.form.controls.endDate.setValue(this.model.endDate ? this.model.endDate : null);
            this.form.controls.endHour.setValue(DateTimeShiftFilterComponent.getCurrentFullHour());
            this.setModelHour(DateTimeShiftFilterComponent.getCurrentFullHour(), 'end');
        }, 600);
    }

    private iniSubscription() {
        this.subscription = this.shiftService.getAll().subscribe(
            allShiftGroups => {
                this.shiftService.upsertManyShiftGroupsInCache (allShiftGroups);
            },
            err => {
                this.throwErrorMsg(err);
            }
        );
    }

    private throwErrorMsg(err: any) {
        let msg;

        if (err.error && err.error.message !== null) {
            msg = err.error.message !== undefined ? err.error.message : err.error;
        } else {
            msg = err.message;
        }

        this.toast.showError(msg);
    }

    private getTimeOptions(): Observable<any[]>  {
        if (this.shiftHourOptions && this.shiftHourOptions.length > 0) {
            return of(this.shiftHourOptions);
        }
        return of(this.getHourOptions());
    }
}
