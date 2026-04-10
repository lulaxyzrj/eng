import {LabelPipe} from './pipes/filter.pipe';
import {CUSTOM_ELEMENTS_SCHEMA, NgModule} from '@angular/core';
import {DecimalPipe} from '@angular/common';
import {SharedCommonModule} from './shared-common.module';
import {SelectComponent} from './components/select/select.component';
import {MultiSelectComponent} from './components/multi-select/multi-select.component';
import {CheckboxFilterComponent} from './components/checkbox-filter/checkbox-filter.component';
import {TranslateModule} from '@ngx-translate/core';
import {LoadingAnimationComponent} from './components/loading-animation/loading-animation.component';
import {TimeTrackerComponent} from './components/time-tracker/time-tracker.component';
import {ProgressBarModule} from 'primeng/progressbar';

@NgModule({
    imports: [SharedCommonModule, TranslateModule, ProgressBarModule],
    exports: [SharedCommonModule, SelectComponent, MultiSelectComponent,
        CheckboxFilterComponent, LoadingAnimationComponent,
        TranslateModule, TimeTrackerComponent,
        ProgressBarModule],
    schemas: [CUSTOM_ELEMENTS_SCHEMA],
    providers: [DecimalPipe],
    declarations: [SelectComponent, MultiSelectComponent,
        CheckboxFilterComponent, LoadingAnimationComponent, LabelPipe,
        TimeTrackerComponent]
})
export class SharedModule {
    static forRoot() {
        return {
            ngModule: SharedModule
        };
    }
}
