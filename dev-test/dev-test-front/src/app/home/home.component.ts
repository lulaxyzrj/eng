import { Component, OnInit } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Location } from '@angular/common';

@Component({
    selector: 'home',
    templateUrl: './home.component.html',
    styleUrls: ['./home.component.scss'],
})
export class HomeComponent implements OnInit {

    
    constructor(public translate: TranslateService,
                private _location: Location) {
    }

    ngOnInit(): void {

    }

    back() {
        this._location.back();
    }
}
