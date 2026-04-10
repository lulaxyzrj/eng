import { Component, OnInit, OnDestroy, EventEmitter } from '@angular/core';
import { FieldType } from '@ngx-formly/core';
import { Subject } from 'rxjs';
import { takeUntil, startWith, debounceTime, distinctUntilChanged, switchMap, filter } from 'rxjs/operators';
import {TranslateService} from '@ngx-translate/core';

@Component({
    selector: 'grm-select',
    templateUrl: './select.type.component.html',
    styleUrls: ['./select.type.component.scss']
})
export class FormlyFieldSelectComponent extends FieldType implements OnInit, OnDestroy {

    onDestroy$ = new Subject<void>();
    search$ = new EventEmitter();
    options$;

    constructor(public translate: TranslateService) {
        super();
    }

    ngOnInit() {
        if (this.to.serverSideSearch) {
            this.options$ = this.search$.pipe(
                takeUntil(this.onDestroy$),
                startWith(''),
                filter(v => v !== null),
                debounceTime(200),
                distinctUntilChanged(),
                switchMap(this.to.search$),
            );
        } else {
            this.options$ = this.to.options$;
        }

        if (!this.to.onChange) {
            this.to.onChange = (e: any) => console.log(e);
        }

        if (this.to.closeOnSelect === null || this.to.closeOnSelect === undefined) {
            this.to.closeOnSelect = true;
        }

        this.options$.subscribe();
    }

    ngOnDestroy() {
        this.onDestroy$.complete();
    }

}
