// Theme colors for the application
const themeColors = {
    // Neon color palette for arcade-style UI
    neonPalette: [
        '#00FFFF', // Cyan
        '#FF00FF', // Magenta
        '#FFFF00', // Yellow
        '#00FF00', // Lime
        '#FF1493', // Deep Pink
        '#00BFFF', // Deep Sky Blue
        '#FF4500', // Orange Red
        '#7FFF00', // Chartreuse
        '#FF00FF', // Fuchsia
        '#00FFFF', // Aqua
        '#FFD700', // Gold
        '#FF6347', // Tomato
        '#8A2BE2', // Blue Violet
        '#32CD32', // Lime Green
        '#FF69B4', // Hot Pink
        '#1E90FF', // Dodger Blue
        '#ADFF2F', // Green Yellow
        '#FF8C00', // Dark Orange
        '#BA55D3', // Medium Orchid
        '#00FA9A'  // Medium Spring Green
    ],
    
    // Get a subset of neon colors
    getNeonPalette: function(count) {
        // If count is greater than available colors, we'll cycle through them
        const colors = [];
        for (let i = 0; i < count; i++) {
            colors.push(this.neonPalette[i % this.neonPalette.length]);
        }
        return colors;
    },
    
    // Primary theme colors
    primary: '#4e73df',
    success: '#1cc88a',
    info: '#36b9cc',
    warning: '#f6c23e',
    danger: '#e74a3b',
    secondary: '#858796',
    light: '#f8f9fc',
    dark: '#5a5c69',
    
    // Get a color by name
    getColor: function(name) {
        return this[name] || this.primary;
    },
    
    // Get a random color from the neon palette
    getRandomNeonColor: function() {
        const index = Math.floor(Math.random() * this.neonPalette.length);
        return this.neonPalette[index];
    }
};
