import {Component, Input} from '@angular/core';

@Component({
    selector: 'loading-animation',
    templateUrl: './loading-animation.component.html',
    styleUrls: ['./loading-animation.component.scss']
})
export class LoadingAnimationComponent {

    @Input() message: string;

    constructor() {}
}
