// Using themeColors from theme_colors.js

class ChartUtilities {
    static getDefaultConfig() {
        return {
            backgroundColor: 'rgba(30, 30, 30, 0.9)',
            fontColor: 'rgba(255, 255, 255, 0.87)',
            gridColor: 'rgba(255, 255, 255, 0.1)',
            tickColor: 'rgba(255, 255, 255, 0.6)',
            neonPalette: themeColors.getNeonPalette(10)
        };
    }

    static applyDarkTheme(chart) {
        const config = this.getDefaultConfig();

        // Apply dark theme to chart
        const options = chart.options;

        // Set common options
        if (options.plugins && options.plugins.legend) {
            options.plugins.legend.labels.color = config.fontColor;
        }

        if (options.plugins && options.plugins.tooltip) {
            options.plugins.tooltip.backgroundColor = config.backgroundColor;
            options.plugins.tooltip.titleColor = config.fontColor;
            options.plugins.tooltip.bodyColor = config.fontColor;
            options.plugins.tooltip.borderColor = '#333';
            options.plugins.tooltip.borderWidth = 1;
        }

        // Set scales options for line and bar charts
        if (options.scales) {
            if (options.scales.x) {
                options.scales.x.grid.color = config.gridColor;
                options.scales.x.ticks.color = config.tickColor;
            }

            if (options.scales.y) {
                options.scales.y.grid.color = config.gridColor;
                options.scales.y.ticks.color = config.tickColor;
                if (options.scales.y.title) {
                    options.scales.y.title.color = config.tickColor;
                }
            }
        }

        chart.update();
    }

    static createFilterableLegend(chart, container, filterContainer = null) {
        // Clear existing legends
        container.innerHTML = '';
        if (filterContainer) filterContainer.innerHTML = '';

        // Create clickable legend for each dataset
        chart.data.datasets.forEach((dataset, index) => {
            // Create legend item
            const legendItem = document.createElement('div');
            legendItem.className = 'legend-item';
            legendItem.dataset.index = index;

            const colorBox = document.createElement('div');
            colorBox.className = 'legend-color';
            colorBox.style.backgroundColor = dataset.borderColor || dataset.backgroundColor;

            const legendText = document.createElement('span');
            legendText.textContent = dataset.label;

            legendItem.appendChild(colorBox);
            legendItem.appendChild(legendText);
            container.appendChild(legendItem);

            // Toggle dataset visibility on click
            legendItem.addEventListener('click', () => {
                const isDatasetVisible = chart.isDatasetVisible(index);
                chart.setDatasetVisibility(index, !isDatasetVisible);
                legendItem.classList.toggle('inactive', isDatasetVisible);

                // Update related filter checkbox if it exists
                if (filterContainer) {
                    const checkbox = filterContainer.querySelector(`#equipment-${index}`);
                    if (checkbox) checkbox.checked = !isDatasetVisible;
                }

                chart.update();
            });

            // Create filter checkbox if filter container provided
            if (filterContainer) {
                const checkboxDiv = document.createElement('div');
                checkboxDiv.className = 'form-check form-check-inline';

                const checkbox = document.createElement('input');
                checkbox.className = 'form-check-input';
                checkbox.type = 'checkbox';
                checkbox.id = `equipment-${index}`;
                checkbox.value = dataset.label;
                checkbox.checked = true;

                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = `equipment-${index}`;
                label.textContent = dataset.label;

                checkboxDiv.appendChild(checkbox);
                checkboxDiv.appendChild(label);
                filterContainer.appendChild(checkboxDiv);

                // Toggle dataset visibility on checkbox change
                checkbox.addEventListener('change', function() {
                    chart.setDatasetVisibility(index, this.checked);
                    legendItem.classList.toggle('inactive', !this.checked);
                    chart.update();
                });
            }
        });
    }
}

// Enhanced table utilities
class TableUtilities {
    static applyRowHighlighting(tableSelector, conditionCallback, highlightClass) {
        const table = document.querySelector(tableSelector);
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            if (conditionCallback(row)) {
                row.classList.add(highlightClass);
            }
        });
    }

    static makeSortable(tableSelector) {
        const table = document.querySelector(tableSelector);
        if (!table) return;

        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            if (header.classList.contains('no-sort')) return;

            header.style.cursor = 'pointer';
            header.dataset.sortDirection = 'none';

            // Add sort icon
            const icon = document.createElement('i');
            icon.className = 'bi bi-arrow-down-up ms-1';
            icon.style.fontSize = '0.75rem';
            header.appendChild(icon);

            header.addEventListener('click', () => {
                this.sortTable(table, index, header);
            });
        });
    }

    static sortTable(table, columnIndex, header) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        // Update sorting direction
        const currentDirection = header.dataset.sortDirection;
        const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';

        // Reset all headers
        table.querySelectorAll('th').forEach(th => {
            th.dataset.sortDirection = 'none';
            const icon = th.querySelector('.bi');
            if (icon) icon.className = 'bi bi-arrow-down-up ms-1';
        });

        // Set current header
        header.dataset.sortDirection = newDirection;
        const headerIcon = header.querySelector('.bi');
        if (headerIcon) {
            headerIcon.className = `bi bi-sort-${newDirection === 'asc' ? 'down' : 'up'} ms-1`;
        }

        // Sort rows
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();

            // Check if values are numeric
            const aNum = parseFloat(aValue);
            const bNum = parseFloat(bValue);

            if (!isNaN(aNum) && !isNaN(bNum)) {
                return newDirection === 'asc' ? aNum - bNum : bNum - aNum;
            }

            // Sort as strings
            const comparison = aValue.localeCompare(bValue);
            return newDirection === 'asc' ? comparison : -comparison;
        });

        // Reorder rows
        rows.forEach(row => tbody.appendChild(row));
    }
}

// Temperature monitoring utilities
class TemperatureMonitor {
    constructor(warningThreshold = 70, criticalThreshold = 85) {
        this.warningThreshold = warningThreshold;
        this.criticalThreshold = criticalThreshold;
    }

    getStatusClass(temperature) {
        if (temperature >= this.criticalThreshold) {
            return 'high-temp';
        } else if (temperature >= this.warningThreshold) {
            return 'warning-temp';
        }
        return '';
    }

    getStatusIcon(temperature) {
        if (temperature >= this.criticalThreshold) {
            return '<i class="bi bi-thermometer-high text-danger"></i>';
        } else if (temperature >= this.warningThreshold) {
            return '<i class="bi bi-thermometer-half text-warning"></i>';
        }
        return '<i class="bi bi-thermometer-low text-success"></i>';
    }

    checkTemperatures(selector = '[data-temperature]') {
        const elements = document.querySelectorAll(selector);

        elements.forEach(el => {
            const temp = parseFloat(el.dataset.temperature);
            if (isNaN(temp)) return;

            // Add appropriate class
            el.className = this.getStatusClass(temp);

            // Add icon if it has a container
            const iconContainer = el.querySelector('.temp-icon');
            if (iconContainer) {
                iconContainer.innerHTML = this.getStatusIcon(temp);
            }
        });
    }
}

/**
 * Utility function for fetching dropdown options from the API
 * Used in equipment forms
 */
async function fetchDropdownOptions(field, datalistId) {
    try {
        const response = await fetch(`/api/dropdown-options/${field}`);
        const options = await response.json();

        const datalist = document.getElementById(datalistId);
        if (!datalist) return;

        datalist.innerHTML = '';

        options.forEach(option => {
            const optionEl = document.createElement('option');
            optionEl.value = option;
            datalist.appendChild(optionEl);
        });
    } catch (error) {
        console.error(`Error fetching ${field} options:`, error);
    }
}

// Initialize on document ready - consolidated event listener
document.addEventListener('DOMContentLoaded', function() {
    // Apply sortable tables
    TableUtilities.makeSortable('.sortable-table');

    // Initialize temperature monitor
    const tempMonitor = new TemperatureMonitor();
    tempMonitor.checkTemperatures();

    // Make equipment rows clickable as a whole
    document.querySelectorAll('.equipment-row').forEach(row => {
        row.style.cursor = 'pointer';

        // Clear existing click events, if any
        const oldElement = row.cloneNode(true);
        row.parentNode.replaceChild(oldElement, row);

        oldElement.addEventListener('click', function(e) {
            if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON') {
                const equipmentId = this.dataset.equipmentId;
                if (equipmentId) {
                    window.location.href = `/equipment/${equipmentId}`;
                }
            }
        });
    });

    // Style maintenance table rows
    const tableRows = document.querySelectorAll('.maintenance-table > tbody > tr');
    tableRows.forEach(row => {
        const deleteButton = row.querySelector('.btn-danger');
        if (deleteButton) {
            row.classList.add('saved-row');
        }
    });

    // Add hover effect to action buttons
    const actionButtons = document.querySelectorAll('.actions-col .btn');
    actionButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            const icon = this.querySelector('.bi');
            if (icon) {
                icon.style.color = 'white';
            }
        });
    });

    // Initialize dropdown options for equipment forms
    if (document.getElementById('pump_model_options')) {
        fetchDropdownOptions('pump_model', 'pump_model_options');
        fetchDropdownOptions('oil_type', 'oil_type_options');
        fetchDropdownOptions('pump_owner', 'pump_owner_options');
    }
});