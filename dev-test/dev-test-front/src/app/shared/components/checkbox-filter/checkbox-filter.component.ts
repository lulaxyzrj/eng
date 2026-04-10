import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';

@Component({
    selector: 'grm-checkbox-filter',
    templateUrl: './checkbox-filter.component.html',
    styleUrls: ['./checkbox-filter.component.scss']
})
export class CheckboxFilterComponent implements OnInit {

    @Input() checkedList: any;
    @Output() selectedValues = new EventEmitter();

    constructor() {}

    ngOnInit() {
    }

    setValue(index) {
        this.checkedList[index].isSelected = !this.checkedList[index].isSelected;
        this.feedback();
    }

    clear() {
        for (let i = 0; i < this.checkedList.length; i++) {
            this.checkedList[i].isSelected = false;
        }
        this.feedback();
    }

    feedback() {
        const values = this.checkedList
            .filter(obj => obj.isSelected)
            .map(({ isSelected, ...rest }) => rest);

        this.selectedValues.emit(values);
    }
}
