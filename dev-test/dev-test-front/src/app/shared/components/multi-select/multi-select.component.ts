import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';

@Component({
    selector: 'grm-multi-select',
    templateUrl: './multi-select.component.html',
    styleUrls: ['./multi-select.component.scss']
})
export class MultiSelectComponent implements OnInit {

    @Input() data: any;
    @Input() placeHolder: string;
    @Output() selectedValues = new EventEmitter();
    @Input() clearValues: EventEmitter<boolean>;

    selectedTags: any;

    constructor() {
    }

    ngOnInit() {
        if (this.clearValues) {
            this.clearValues.subscribe(data => {
                this.selectedTags = [];
                this.sendFeedback();
            });
        }
    }

    onChangeTags() {
        this.sendFeedback();
    }

    sendFeedback() {
        this.selectedValues.emit(this.selectedTags);
    }
}
