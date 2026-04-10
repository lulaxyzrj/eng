import { NgModule } from '@angular/core';
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
import { OverlayPanelModule } from 'primeng/overlaypanel';
import { ToolbarModule } from 'primeng/toolbar';
import { TooltipModule } from 'primeng/tooltip';
import { BreadcrumbModule } from 'primeng/breadcrumb';
import { AccordionModule } from 'primeng/accordion';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ToastModule } from 'primeng/toast';
import { VirtualScrollerModule } from 'primeng/virtualscroller';
import { MultiSelectModule } from 'primeng/multiselect';
import { DynamicDialogModule, DialogService } from 'primeng/dynamicdialog';
import { MessageService, ConfirmationService } from 'primeng/api';
import { DialogModule } from 'primeng/dialog';
import { DataViewModule } from 'primeng/dataview';
import { InputTextModule } from 'primeng/inputtext';
import { TableModule } from 'primeng/table';
import { SelectButtonModule } from 'primeng/selectbutton';
import { CardModule } from 'primeng/card';
import { InputSwitchModule } from 'primeng/inputswitch';
import { TabViewModule } from 'primeng/tabview';
import { ListboxModule } from 'primeng/listbox';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { CheckboxModule } from 'primeng/checkbox';
import {ToggleButtonModule} from 'primeng/togglebutton';
import {MenuModule} from 'primeng/menu';
import {ChartModule} from 'primeng/chart';
import {ColorPickerModule} from 'primeng/colorpicker';
import {TreeModule} from 'primeng/tree';
import {TreeTableModule} from 'primeng/treetable';
import { ScrollPanelModule } from 'primeng/scrollpanel';
import { RatingModule } from 'primeng/rating';

@NgModule({
    exports: [
        DropdownModule,
        CalendarModule,
        OverlayPanelModule,
        ToolbarModule,
        TooltipModule,
        BreadcrumbModule,
        AccordionModule,
        ChartModule,
        ProgressSpinnerModule,
        ToastModule,
        VirtualScrollerModule,
        MultiSelectModule,
        DynamicDialogModule,
        DialogModule,
        DataViewModule,
        InputTextModule,
        TableModule,
        SelectButtonModule,
        CardModule,
        InputSwitchModule,
        TabViewModule,
        ListboxModule,
        ConfirmDialogModule,
        CheckboxModule,
        ToggleButtonModule,
        MenuModule,
        ColorPickerModule,
        TreeModule,
        TreeTableModule,
        ScrollPanelModule,
        RatingModule
    ],
    providers: [DialogService, MessageService, ConfirmationService]
})
export class CommonPrimengModule { }
