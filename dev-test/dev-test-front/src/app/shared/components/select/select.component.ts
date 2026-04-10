import { Component, OnInit, Input, Output , EventEmitter } from '@angular/core';

@Component({
  selector: 'grm-select',
  templateUrl: './select.component.html',
  styleUrls: ['./select.component.scss']
})
export class SelectComponent implements OnInit {

  @Input() data: any;
  @Input() defaultText: string;
  @Input() textKeyValue: string;
  @Output() valueSelected = new EventEmitter();
  selected: any;
  filtered: any;

  feedback() {
    console.log(this.selected);
    this.valueSelected.emit(this.selected);
  }

  constructor() { }

  ngOnInit() {
  }
}
