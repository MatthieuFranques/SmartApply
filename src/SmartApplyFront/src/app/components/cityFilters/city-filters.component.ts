import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface CityCount {
  name: string;
  count: number;
}

@Component({
  selector: 'app-city-filters',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './city-filters.component.html',
  styleUrls: ['./city-filters.component.scss'],
})
export class CityFiltersComponent {
  @Input() cities: CityCount[] = [];
  @Input() selected = 'all';
  @Input() total = 0;
  @Output() citySelected = new EventEmitter<string>();
}
