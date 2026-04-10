import {ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnInit} from '@angular/core';
import {TimeTrackerFormat} from './time-tracker-format';
import {interval} from 'rxjs';

@Component({
    selector: 'grm-time-tracker',
    templateUrl: './time-tracker.component.html',
    styleUrls: ['./time-tracker.component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class TimeTrackerComponent implements OnInit {

    @Input() bold: boolean;
    @Input() startDate: number | null;
    @Input() format = TimeTrackerFormat.HH_MI_SS;
    @Input() fontSize = 12;
    @Input() endDate: number | null;
    @Input() fontColor = '#000000';

    formattedTime: string;

    constructor(private changeDetector: ChangeDetectorRef) {
    }

    ngOnInit() {
        if (!this.endDate) {
            interval(1000).subscribe(() => {
                const currentDate = new Date();
                this.getFormattedTime(currentDate);
                this.changeDetector.detectChanges();
            });
        } else {
            this.getFormattedTime(new Date(this.endDate));
        }
    }

    getFormattedTime(endDate: Date) {
        switch (this.format) {
            case TimeTrackerFormat.DD_HH_MI_SS:
                this.formattedTime = this.transformDDHHMMSS(this.calculateDiff(endDate));
                break;
            case TimeTrackerFormat.DD_HH_MI:
                this.formattedTime = this.transformDDHHMM(this.calculateDiff(endDate));
                break;
            case TimeTrackerFormat.HH_MI_SS:
                this.formattedTime = this.transformHHMMSS(this.calculateDiff(endDate));
                break;
            case TimeTrackerFormat.MI_SS:
                this.formattedTime = this.transformMMSS(this.calculateDiff(endDate));
                break;
            default:
                this.formattedTime = this.transformHHMMSS(this.calculateDiff(endDate));
                break;
        }
    }

    calculateDiff(endDate: Date) {
        if (this.startDate) {
            const convertedStartDate = new Date(this.startDate);
            return endDate.getTime() - convertedStartDate.getTime();
        }
        return 0;
    }

    transformMMSS(millis: number): string {
        const minutes = Math.floor(millis / 60000);
        const seconds = Math.floor(((millis % 60000) / 1000));
        return (minutes < 10 ? '0' : '') + minutes + 'm:' + (seconds < 10 ? '0' : '') + seconds + 's';
    }

    transformHHMMSS(millis: number): string {
        const hours = Math.floor((millis / (1000 * 60 * 60)));
        const minutes = Math.floor((millis / (1000 * 60)) % 60);
        const seconds = Math.floor((millis / 1000) % 60);

        return (hours < 10 ? '0' : '') + hours + 'h:' + (minutes < 10 ? '0' : '') + minutes + 'm:' + (seconds < 10 ? '0' : '') + seconds + 's';
    }

    transformDDHHMM(millis: number): string {
        const days = Math.floor(millis / 24 / 3600 / 1000);
        const hours = Math.floor((millis / (1000 * 60 * 60)) % 24);
        const minutes = Math.floor((millis / (1000 * 60)) % 60);

        return days + 'd ' + (hours < 10 ? '0' : '') + hours + 'h:' + (minutes < 10 ? '0' : '') + minutes + 'm';
    }

    transformDDHHMMSS(millis: number): string {
        const days = Math.floor(millis / 24 / 3600 / 1000);
        const hours = Math.floor((millis / (1000 * 60 * 60)) % 24);
        const minutes = Math.floor((millis / (1000 * 60)) % 60);
        const seconds = Math.floor((millis / 1000) % 60);

        return days + 'd ' + (hours < 10 ? '0' : '') + hours + 'h:' + (minutes < 10 ? '0' : '') + minutes + 'm:' + (seconds < 10 ? '0' : '') + seconds + 's';
    }
}
