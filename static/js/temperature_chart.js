// Register a custom plugin for rounded corners on doughnut charts
Chart.register({
    id: 'roundedDoughnut',
    beforeDraw: function(chart) {
        if (chart.config.type !== 'doughnut') {
            return;
        }

        const ctx = chart.ctx;
        ctx.save();

        ctx.shadowColor = 'rgba(255, 255, 255, 0.5)';
        ctx.shadowBlur = 15;

        ctx.restore();
    }
});
function generateUniqueNeonColors(count) {
    const neonColors = themeColors.getNeonPalette(count);

    if (count > neonColors.length) {
        for (let i = neonColors.length; i < count; i++) {
            const hue = (i * 137) % 360;
            const color = `hsl(${hue}, 100%, 70%)`;
            neonColors.push(color);
        }
    }

    return neonColors.slice(0, count);
}

function setupTemperatureChart(data) {
    const tempCtx = document.getElementById('temperatureChart').getContext('2d');
    const legendContainer = document.getElementById('tempChartLegend');
    const equipmentFiltersContainer = document.getElementById('equipmentFilters');

    if (!tempCtx || !legendContainer || !equipmentFiltersContainer) return;

    const datasets = data.temperature_chart.datasets;
    const equipmentNames = datasets.map(dataset => dataset.label);

    const uniqueColors = generateUniqueNeonColors(datasets.length);

    datasets.forEach((dataset, index) => {
        const color = uniqueColors[index];
        dataset.borderColor = color;
        dataset.borderWidth = 2;
        dataset.pointRadius = 4;
        dataset.pointHoverRadius = 6;
        dataset.tension = 0.4; 

        const glowColor = color.replace('1)', '0.2)');
        dataset.backgroundColor = glowColor;

        dataset.pointBackgroundColor = color;
        dataset.pointBorderColor = '#121212';
        dataset.pointBorderWidth = 1;
        dataset.pointHitRadius = 1;

        dataset.borderWidth = 2.5;
    });

    legendContainer.innerHTML = '';
    equipmentNames.forEach((name, index) => {
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.dataset.index = index;

        const colorBox = document.createElement('div');
        colorBox.className = 'legend-color';
        colorBox.style.backgroundColor = uniqueColors[index];
        colorBox.style.boxShadow = `0 0 5px ${uniqueColors[index]}`;

        const legendText = document.createElement('span');
        legendText.textContent = name;

        legendItem.appendChild(colorBox);
        legendItem.appendChild(legendText);
        legendContainer.appendChild(legendItem);
    });

    // Create equipment filter checkboxes with matching colors
    equipmentFiltersContainer.innerHTML = '';
    equipmentNames.forEach((name, index) => {
        const checkboxDiv = document.createElement('div');
        checkboxDiv.className = 'form-check form-check-inline';

        const checkbox = document.createElement('input');
        checkbox.className = 'form-check-input';
        checkbox.type = 'checkbox';
        checkbox.id = `equipment-${index}`;
        checkbox.value = name;
        checkbox.checked = true;
        checkbox.style.backgroundColor = uniqueColors[index].replace('1)', '0.5)');
        checkbox.style.borderColor = uniqueColors[index];

        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = `equipment-${index}`;
        label.textContent = name;

        checkboxDiv.appendChild(checkbox);
        checkboxDiv.appendChild(label);
        equipmentFiltersContainer.appendChild(checkboxDiv);
    });

    // Create temperature chart with enhanced styling
    Chart.defaults.plugins.tooltip.itemSort = (a, b) => b.parsed.y - a.parsed.y;

    const temperatureChart = new Chart(tempCtx, {
        type: 'line',
        data: data.temperature_chart,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: false // Using custom legend
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 30, 30, 0.9)',
                    titleColor: 'rgba(255, 255, 255, 0.87)',
                    bodyColor: 'rgba(255, 255, 255, 0.87)',
                    borderColor: '#333',
                    borderWidth: 1,
                    padding: 8,
                    displayColors: true,
                    usePointStyle: true,
                    position: 'average',
                    xAlign: 'left',
                    yAlign: 'center',
                    caretPadding: 10,
                    caretSize: 0, 
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y + '°C';
                            }
                            return label;
                        },
                        afterBody: function() {
                            return '';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    suggestedMin: 60,
                    suggestedMax: 90,
                    title: {
                        display: true,
                        text: 'Temperature (°C)',
                        color: 'rgba(255, 255, 255, 0.6)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.6)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.6)'
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });

    // Handle legend click events
    legendContainer.addEventListener('click', (e) => {
        const legendItem = e.target.closest('.legend-item');
        if (!legendItem) return;

        const index = parseInt(legendItem.dataset.index);
        const isDatasetVisible = temperatureChart.isDatasetVisible(index);

        // Toggle visibility
        const newVisibility = !isDatasetVisible;
        temperatureChart.setDatasetVisibility(index, newVisibility);

        // Toggle the inactive class - when dataset is NOT visible, add the inactive class
        if (newVisibility) {
            // Dataset is now visible, remove inactive class (full opacity)
            legendItem.classList.remove('inactive');
        } else {
            // Dataset is now hidden, add inactive class (0.5 opacity)
            legendItem.classList.add('inactive');
        }

        // Update the checkbox state to match
        const checkbox = document.querySelector(`#equipment-${index}`);
        if (checkbox) checkbox.checked = newVisibility;

        temperatureChart.update();
    });

    // Handle filter checkbox changes
    document.querySelectorAll('#equipmentFilters input[type="checkbox"]').forEach((checkbox, index) => {
        checkbox.addEventListener('change', function() {
            const legendItem = document.querySelector(`.legend-item[data-index="${index}"]`);
            if (!legendItem) return;

            // Set dataset visibility based on checkbox state
            temperatureChart.setDatasetVisibility(index, this.checked);

            // Toggle the inactive class - when dataset is NOT visible, add the inactive class
            if (this.checked) {
                // Dataset is visible, remove inactive class (full opacity)
                legendItem.classList.remove('inactive');
            } else {
                // Dataset is hidden, add inactive class (0.5 opacity)
                legendItem.classList.add('inactive');
            }

            temperatureChart.update();
        });
    });

    // Ensure all datasets are visible initially and legend items don't have inactive class
    datasets.forEach((_, index) => {
        temperatureChart.setDatasetVisibility(index, true);
        const legendItem = document.querySelector(`.legend-item[data-index="${index}"]`);
        if (legendItem) {
            legendItem.classList.remove('inactive');
        }
    });

    return temperatureChart;
}

// Enhanced service chart with glow effects and rounded corners
function setupServiceChart(data) {
    const serviceCtx = document.getElementById('serviceChart')?.getContext('2d');
    if (!serviceCtx) return;

    // Generate neon colors with glow effect
    const neonColors = generateUniqueNeonColors(data.service_chart.labels.length);

    // Create shadow canvas for glow effect
    const createGlowEffect = () => {
        // Add shadow to the canvas for the glow effect
        const ctx = serviceCtx;
        ctx.shadowBlur = 15;
        ctx.shadowColor = 'rgba(255, 255, 255, 0.5)';
    };

    // Ensure the chart is responsive
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;

    // Apply glowing neon colors
    data.service_chart.datasets[0].backgroundColor = neonColors;
    data.service_chart.datasets[0].borderColor = '#1e1e1e';
    data.service_chart.datasets[0].borderWidth = 1;

    // Add hover effects
    data.service_chart.datasets[0].hoverOffset = 15;
    data.service_chart.datasets[0].hoverBorderWidth = 2;
    data.service_chart.datasets[0].hoverBorderColor = neonColors.map(color => color.replace('1)', '0.9)'));

    // Create a plugin for rounded corners and glow effects
    const roundedCornerPlugin = {
        id: 'roundedCorner',
        beforeDraw: function() {
            createGlowEffect();
        },
        afterDraw: function(chart) {
            const ctx = chart.ctx;
            ctx.save();
            ctx.shadowBlur = 0; // Reset shadow for legend

            // Add glow to legend items
            const legendItems = document.querySelectorAll('.chart-legend-item');
            legendItems.forEach((item, i) => {
                const color = neonColors[i];
                item.style.textShadow = `0 0 5px ${color}`;

                const colorBox = item.querySelector('.color-box');
                if (colorBox) {
                    colorBox.style.boxShadow = `0 0 8px ${color}`;
                }
            });

            ctx.restore();
        }
    };

    const serviceChart = new Chart(serviceCtx, {
        type: 'doughnut',
        data: data.service_chart,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                roundedCorner: {
                    enabled: true
                },
                legend: {
                    position: 'bottom',
                    align: 'center',
                    display: true,
                    fullWidth: true,
                    labels: {
                        color: 'rgba(255, 255, 255, 0.87)',
                        padding: 12, 
                        usePointStyle: true,
                        boxWidth: 30, 
                        boxHeight: 12,
                        font: {
                            size: 14
                        },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map(function(label, i) {
                                    return {
                                        text: label,
                                        fillStyle: neonColors[i],
                                        strokeStyle: '#333',
                                        lineWidth: 1,
                                        hidden: !chart.getDataVisibility(i),
                                        index: i,
                                        pointStyle: 'rectRounded',
                                        rotation: 0
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 30, 30, 0.9)',
                    titleColor: 'rgba(255, 255, 255, 0.87)',
                    bodyColor: 'rgba(255, 255, 255, 0.87)',
                    borderColor: '#333',
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.formattedValue;
                            return `${label}: ${value}`;
                        }
                    }
                }
            },
            cutout: '80%', // Adjusted thickness for better visibility
            borderRadius: 20, // Rounded ends
            animation: {
                animateRotate: true,
                animateScale: true
            },
            layout: {
                padding: {
                    top: 10,
                    bottom: 50, // Add even more padding at the bottom for larger legend
                    left: 20,
                    right: 20
                }
            },
            elements: {
                arc: {
                    borderRadius: 30, // Increase border radius for more rounded ends
                    borderWidth: 1,
                    borderColor: '#1e1e1e',
                    borderJoinStyle: 'round'
                }
            }
        },
        plugins: [roundedCornerPlugin]
    });

    // Add custom CSS for the legend items
    // We need to wait for the chart to render the legend
    setTimeout(() => {
        const legendContainer = document.querySelector('#serviceChart').closest('.card-body').querySelector('.chartjs-legend');
        if (legendContainer) {
            const items = legendContainer.querySelectorAll('li');
            items.forEach((item, index) => {
                item.classList.add('chart-legend-item');
                const span = item.querySelector('span');
                if (span) {
                    const color = neonColors[index];
                    span.classList.add('color-box');
                    span.style.boxShadow = `0 0 8px ${color}`;
                }
            });
        }

        // Also add a class to all legend items for styling
        document.querySelectorAll('.chartjs-legend li').forEach((item, index) => {
            item.classList.add('chart-legend-item');
            item.style.textShadow = `0 0 5px ${neonColors[index % neonColors.length]}`;
        });
    }, 100);

    return serviceChart;
}