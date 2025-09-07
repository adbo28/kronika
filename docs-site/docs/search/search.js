/**
 * Pokročilé vyhledávání kroniky - Implementační logika
 * Kompatibilní s MkDocs prostředím
 */

// ============================================================================
// GLOBÁLNÍ DATOVÉ STRUKTURY
// ============================================================================

/**
 * Hlavní index dat pro vyhledávání
 */
let searchIndex = {
    years: new Map(),        // year -> count
    houses: new Map(),       // houseNumber -> count
    names: new Map(),        // name -> count
    keywords: new Map(),     // keyword -> count
    yearRange: { min: 1800, max: 2024 },
    yearPresetCounts: new Map() // presetLabel -> count
};

/**
 * Metadata obsahu pro filtrování
 */
let contentData = new Map(); // contentId -> { chapter, title, years[], houses[], names[], keywords[], url }

/**
 * Konfigurační objekty
 */
const searchConfig = {
    debounceDelay: 300,
    maxVisibleBadges: 20,
    histogramBins: 50,
    intensityLevels: 5,
    yearPresets: [
        { label: 'Před r. 1700', from: 0, to: 1699 },
        { label: '18. století', from: 1700, to: 1799 },
        { label: '19. století', from: 1800, to: 1899 },
        { label: 'Začátek 20. století', from: 1900, to: 1913 },
        { label: 'První sv. válka', from: 1914, to: 1918 },
        { label: 'Meziválečné období', from: 1919, to: 1938 },
        { label: 'Druhá sv. válka', from: 1939, to: 1945 },
        { label: 'Poválečná historie', from: 1946, to: 9999 }
    ]
};

// ============================================================================
// HLAVNÍ TŘÍDA PRO SPRÁVU FILTRŮ
// ============================================================================

class ChronicleSearchManager {
    constructor() {
        this.activeFilters = {
            years: new Set(),        // Set<string>
            houses: new Set(),  // Set<string>
            names: new Set(),   // Set<string>
            keywords: new Set() // Set<string>
        };
        
        this.activeTab = 'years';
        this.debounceTimers = new Map();
        this.currentResults = [];
        this.uiElements = {};
        
        this.init();
    }
    
    async init() {
        this.uiElements = {
            tabButtons: new Map(),
            tabPanels: new Map(),
            inputs: new Map()
        };

        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            const sectionId = button.dataset.filter;
            if (!sectionId) return;

            this.uiElements.tabButtons.set(sectionId, button);
            button.addEventListener('click', () => this.switchTab(sectionId));
            
            const panelId = button.getAttribute('aria-controls');
            const panel = document.getElementById(panelId);
            if (panel) {
                this.uiElements.tabPanels.set(sectionId, panel);
                const input = panel.querySelector('.filter-input');
                if(input) {
                    this.uiElements.inputs.set(sectionId, input);
                    input.addEventListener('input', (e) => this.handleSearchInput(sectionId, e.target.value));
                }
            }
        });
        
        this.switchTab(this.activeTab);
        await this.loadSearchData('global_index.json');
    }
    
    // ========================================================================
    // SPRÁVA FILTRŮ
    // ========================================================================
    
    addTextFilter(type, value) {
        if (!this.activeFilters[type]) return;
        this.activeFilters[type].add(value);
        this._rerenderAllComponents();
    }
    
    removeTextFilter(type, value) {
        if (this.activeFilters[type]) {
            this.activeFilters[type].delete(value);
        }
        this._rerenderAllComponents();
    }
    
    clearAllFilters() {
        this.activeFilters.years = new Set();
        this.activeFilters.houses = new Set();
        this.activeFilters.names = new Set();
        this.activeFilters.keywords = new Set();
        this._rerenderAllComponents();
    }
    
    // ========================================================================
    // VÝPOČET VÝSLEDKŮ
    // ========================================================================
    

    _rerenderAllComponents() {
        this.renderActiveBadges();
        this.renderAllBadges();
        this.renderChapterHeatmap();
    }

    // ========================================================================
    // TAB A INPUT HANDLING
    // ========================================================================
    
    switchTab(sectionId) {
        this.activeTab = sectionId;
        this.uiElements.tabButtons.forEach((button, id) => {
            const isActive = id === sectionId;
            button.classList.toggle('active', isActive);
            button.setAttribute('aria-selected', isActive);
        });
        this.uiElements.tabPanels.forEach((panel, id) => {
            panel.classList.toggle('active', id === sectionId);
        });
        // Render badges for all tabs to reflect cross-filtering
        this.renderAllBadges();
    }
    
    handleSearchInput(filterType, inputValue) {
        const term = inputValue.trim();
        this.renderBadges(filterType, term);
    }
    
    // ========================================================================
    // HISTOGRAM A YEAR SLIDER
    // ========================================================================
    
    
    // ========================================================================
    // BADGE A TOOLTIP MANAGEMENT
    // ========================================================================
    
    createBadge(text, count, isActive = false) {
        const badge = document.createElement('span');
        badge.className = 'badge';
        if (isActive) {
            badge.classList.add('active');
        }
        badge.setAttribute('onclick', 'toggleBadge(this)');
        badge.innerHTML = `${text} <span class="badge-count">(${count})</span>`;
        return badge;
    }
    
    handleBadgeClick(badgeElement) {
        const filterType = badgeElement.closest('.tab-panel').id.replace('tab-panel-', '');
        const textContent = badgeElement.textContent.replace(/\s*\(\d+\)$/, '');

        if (filterType === 'years') {
            const from = badgeElement.dataset.from;
            const to = badgeElement.dataset.to;
            const yearRangeString = `${from}-${to}`;
            
            if (this.activeFilters.years.has(yearRangeString)) {
                this.activeFilters.years.delete(yearRangeString);
            } else {
                this.activeFilters.years.add(yearRangeString);
            }
            this._rerenderAllComponents();

        } else {
            const value = filterType === 'houses' ? textContent.replace('č.p. ', '') : textContent;
            this.addTextFilter(filterType, value);
        }
    }

    renderAllBadges() {
        this.renderYearBadges();
        ['houses', 'names', 'keywords'].forEach(type => {
            const input = this.uiElements.inputs.get(type);
            this.renderBadges(type, input?.value || '');
        });
    }


    renderActiveBadges() {
        const container = document.querySelector('.breadcrumb-filters');
        if (!container) return;

        container.innerHTML = '';

        // Render text filters
        ['years', 'houses', 'names', 'keywords'].forEach(filterType => {
            const activeFilters = this.activeFilters[filterType];
            activeFilters.forEach(value => {
                const count = searchIndex[filterType].get(value) || 0;
                const displayText = filterType === 'houses' ? `č.p. ${value}` : value;
                const breadcrumb = document.createElement('span');
                breadcrumb.className = 'breadcrumb-tag';
                breadcrumb.innerHTML = `${displayText} <span class="breadcrumb-tag-remove" onclick="removeBreadcrumb(this, '${filterType}', '${value}')">×</span>`;
                container.appendChild(breadcrumb);
            });
        });
    }

    renderChapterHeatmap() {
        const chapterGroups = document.querySelectorAll('.chapter-group');

        const chapterScores = new Map();

        // Initialize scores
        chapterGroups.forEach(group => {
            const dots = group.querySelectorAll('.content-dot');
            dots.forEach(dot => {
                const tooltip = dot.dataset.tooltip;
                if (tooltip) {
                    chapterScores.set(tooltip, 0);
                }
            });
        });

        if (this.hasActiveFilters()) {
            // Calculate scores based on filtered content
            for (const [contentId, contentItem] of contentData.entries()) {
                if (this.contentMatchesFilters(contentItem)) {
                    const chapterTitle = contentItem.title; // Assuming title maps to tooltip
                    if (chapterScores.has(chapterTitle)) {
                        let score = chapterScores.get(chapterTitle) || 0;
                        // Example scoring logic, can be refined
                        score += (contentItem.names.size * 2);
                        score += (contentItem.houses.size * 1);
                        score += (contentItem.keywords.size * 1.5);
                        score += (contentItem.years.size * 1);
                        chapterScores.set(chapterTitle, score);
                    }
                }
            }
        }

        const allScores = [...chapterScores.values()];
        const maxScore = Math.max(...allScores.filter(s => s > 0));

        // Update dot intensity
        chapterGroups.forEach(group => {
            const dots = group.querySelectorAll('.content-dot');
            dots.forEach(dot => {
                const tooltip = dot.dataset.tooltip;
                const score = chapterScores.get(tooltip) || 0;

                // Clear previous intensity
                dot.className = dot.className.replace(/intensity-\d+/g, '').trim();

                if (score > 0 && maxScore > 0) {
                    const intensity = Math.ceil((score / maxScore) * searchConfig.intensityLevels);
                    dot.classList.add(`intensity-${intensity}`);
                    dot.classList.remove('disabled');
                } else if (!this.hasActiveFilters()) {
                    // Reset to default state if no filters are active
                    const originalIntensity = dot.getAttribute('data-original-intensity');
                    if(originalIntensity) {
                       dot.classList.add(originalIntensity);
                    }
                    dot.classList.remove('disabled');
                }
                else {
                    const originalIntensity = dot.getAttribute('data-original-intensity');
                    if (originalIntensity && originalIntensity !== 'disabled') {
                        dot.classList.add(originalIntensity);
                        dot.classList.remove('disabled');
                    } else {
                        dot.classList.add('disabled');
                    }
                }
            });
        });
    }

    hasActiveFilters() {
        return this.activeFilters.years.size > 0 ||
               this.activeFilters.houses.size > 0 ||
               this.activeFilters.names.size > 0 ||
               this.activeFilters.keywords.size > 0;
    }

    contentMatchesFilters(contentItem) {
        // Check year filter
        if (this.activeFilters.years.size > 0) {
            const hasMatchingYear = [...contentItem.years].some(year => {
                for (const range of this.activeFilters.years) {
                    const [from, to] = range.split('-').map(Number);
                    if (year >= from && year <= to) {
                        return true;
                    }
                }
                return false;
            });
            if (!hasMatchingYear) return false;
        }

        // Check house filter
        if (this.activeFilters.houses.size > 0) {
            const hasMatchingHouse = [...this.activeFilters.houses].some(house =>
                contentItem.houses.has(house)
            );
            if (!hasMatchingHouse) return false;
        }

        // Check name filter
        if (this.activeFilters.names.size > 0) {
            const hasMatchingName = [...this.activeFilters.names].some(name =>
                contentItem.names.has(name)
            );
            if (!hasMatchingName) return false;
        }

        // Check keyword filter
        if (this.activeFilters.keywords.size > 0) {
            const hasMatchingKeyword = [...this.activeFilters.keywords].some(keyword =>
                contentItem.keywords.has(keyword)
            );
            if (!hasMatchingKeyword) return false;
        }

        return true;
    }

    renderBadges(filterType, filterTerm = '') {
        const container = document.querySelector(`#tab-panel-${filterType} .badge-container`);
        if (!container) {
            console.error(`Could not find the container for available ${filterType} badges.`);
            return;
        }

        container.innerHTML = '';

        const sourceData = searchIndex[filterType];
        if(!sourceData) return;

        let allItems = [...sourceData.entries()];
        const activeItems = this.activeFilters[filterType];

        // Filter out active items
        allItems = allItems.filter(([name]) => !activeItems.has(name));

        // Cross-filter: only show items that appear in content matching all active filters
        if (this.hasActiveFilters()) {
            allItems = allItems.filter(([name]) => this.itemMatchesCrossFilters(filterType, name));
        }

        if (filterTerm) {
            allItems = allItems.filter(([name]) => name.toLowerCase().includes(filterTerm.toLowerCase()));
        }

        const sortedItems = allItems.sort((a, b) => b[1] - a[1]);
        const isKeywords = filterType === 'keywords';
        const visibleBadges = isKeywords ? sortedItems : sortedItems.slice(0, searchConfig.maxVisibleBadges);

        const moreLabelContainer = container.parentElement;
        let moreLabel = moreLabelContainer.querySelector('.more-items-label');
        if (moreLabel) {
            moreLabel.remove();
        }

        let noResultsLabel = moreLabelContainer.querySelector('.no-results-label');
        if (noResultsLabel) {
            noResultsLabel.remove();
        }

        if (visibleBadges.length === 0 && filterTerm) {
            noResultsLabel = document.createElement('span');
            noResultsLabel.className = 'no-results-label';
            noResultsLabel.textContent = 'žádné položky neodpovídají filtru';
            container.appendChild(noResultsLabel);
            return;
        }


        visibleBadges.forEach(([name, count]) => {
            const badgeText = filterType === 'houses' ? `č.p. ${name}` : name;
            const badgeElement = this.createBadge(badgeText, count);
            container.appendChild(badgeElement);
        });

        const remainingCount = sortedItems.length - visibleBadges.length;
        if (remainingCount > 0 && !isKeywords) {
            moreLabel = document.createElement('span');
            moreLabel.className = 'more-items-label';
            const typeText = filterType === 'houses' ? 'čísel popisných' : 'jmen';
            moreLabel.textContent = `A dalších ${remainingCount} ${typeText}`;
            moreLabelContainer.appendChild(moreLabel);
        }
    }


    itemMatchesCrossFilters(filterType, value) {
        // Check if there's any content that has this value and matches all active filters
        for (const [contentId, contentItem] of contentData) {
            let hasValue = false;
            switch (filterType) {
                case 'houses':
                    hasValue = contentItem.houses.has(value);
                    break;
                case 'names':
                    hasValue = contentItem.names.has(value);
                    break;
                case 'keywords':
                    hasValue = contentItem.keywords.has(value);
                    break;
                case 'years':
                    hasValue = contentItem.years.has(parseInt(value, 10));
                    break;
            }
            if (hasValue && this.contentMatchesFilters(contentItem)) {
                return true;
            }
        }
        return false;
    }


    contentMatchesFiltersExcludingYear(contentItem) {
        // Check house filter
        if (this.activeFilters.houses.size > 0) {
            const hasMatchingHouse = [...this.activeFilters.houses].some(house =>
                contentItem.houses.has(house)
            );
            if (!hasMatchingHouse) return false;
        }

        // Check name filter
        if (this.activeFilters.names.size > 0) {
            const hasMatchingName = [...this.activeFilters.names].some(name =>
                contentItem.names.has(name)
            );
            if (!hasMatchingName) return false;
        }

        // Check keyword filter
        if (this.activeFilters.keywords.size > 0) {
            const hasMatchingKeyword = [...this.activeFilters.keywords].some(keyword =>
                contentItem.keywords.has(keyword)
            );
            if (!hasMatchingKeyword) return false;
        }

        return true;
    }

    
    renderYearBadges() {
        const container = document.querySelector(`#tab-panel-years .badge-container`);
        if (!container) return;

        container.innerHTML = '';

        searchConfig.yearPresets.forEach(preset => {
            const yearRangeString = `${preset.from}-${preset.to}`;
            const isActive = this.activeFilters.years.has(yearRangeString);
            const count = searchIndex.yearPresetCounts.get(preset.label) || 0;

            const badge = this.createBadge(preset.label, count, isActive);
            badge.dataset.from = preset.from;
            badge.dataset.to = preset.to;
            
            if (count === 0 && !isActive) {
                badge.style.display = 'none';
            }

            container.appendChild(badge);
        });
    }
    
    // ========================================================================
    // DATA LOADING A INDEXOVÁNÍ
    // ========================================================================
    
    async loadSearchData(jsonUrl) {
        try {
            const response = await fetch(jsonUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const rawData = await response.json();
            this.buildSearchIndex(rawData);
        } catch (error) {
            console.error("Failed to load search data:", error);
        }
    }
    
    buildSearchIndex(rawData) {
        // Reset existing data
        searchIndex = {
            years: new Map(),
            houses: new Map(),
            names: new Map(),
            keywords: new Map(),
            yearRange: { min: Infinity, max: -Infinity },
            histogram: new Map()
        };
        contentData = new Map();

        if (!rawData || !rawData.entities) {
            console.error("Invalid data structure for search index.", rawData);
            return;
        }

        for (const entityType in rawData.entities) {
            const entities = rawData.entities[entityType];
            let targetMap;
            switch (entityType) {
                case 'NAME':
                    targetMap = searchIndex.names;
                    break;
                case 'ADDRESS_NUMBER':
                    targetMap = searchIndex.houses;
                    break;
                case 'YEAR':
                    targetMap = searchIndex.years;
                    break;
                default:
                    targetMap = searchIndex.keywords;
            }

            for (const entityName in entities) {
                const entity = entities[entityName];
                targetMap.set(entityName, entity.total_count);

                entity.contexts.forEach((context, i) => {
                    const chapter = String(entity.chapters[i] || 'Unknown Chapter');
                    const contentId = chapter;

                    if (!contentData.has(contentId)) {
                        contentData.set(contentId, {
                            chapter: chapter,
                            title: context,
                            years: new Set(),
                            houses: new Set(),
                            names: new Set(),
                            keywords: new Set(),
                            url: `#${entity.anchor_id}`
                        });
                    }

                    const contentItem = contentData.get(contentId);
                    switch (entityType) {
                        case 'NAME':
                            contentItem.names.add(entityName);
                            break;
                        case 'ADDRESS_NUMBER':
                            contentItem.houses.add(entityName);
                            break;
                        case 'YEAR':
                            const year = parseInt(entityName, 10);
                            if (!isNaN(year)) {
                                contentItem.years.add(year);
                                if(year < searchIndex.yearRange.min) searchIndex.yearRange.min = year;
                                if(year > searchIndex.yearRange.max) searchIndex.yearRange.max = year;
                            }
                            break;
                        default:
                            contentItem.keywords.add(entityName);
                    }
                });
            }
        }
        // Compute histogram: year -> number of chapters
        searchIndex.histogram = new Map();
        for (const [contentId, contentItem] of contentData) {
            for (const year of contentItem.years) {
                searchIndex.histogram.set(year, (searchIndex.histogram.get(year) || 0) + 1);
            }
        }

        // Pre-calculate year preset counts from total_counts
        searchIndex.yearPresetCounts = new Map();
        for (const preset of searchConfig.yearPresets) {
            searchIndex.yearPresetCounts.set(preset.label, 0);
        }

        for (const [yearStr, count] of searchIndex.years.entries()) {
            const year = parseInt(yearStr, 10);
            if (isNaN(year)) continue;

            for (const preset of searchConfig.yearPresets) {
                if (year >= preset.from && year <= preset.to) {
                    const currentCount = searchIndex.yearPresetCounts.get(preset.label) || 0;
                    searchIndex.yearPresetCounts.set(preset.label, currentCount + count);
                    break;
                }
            }
        }

        console.log("Search index built:", {searchIndex, contentData});
        this._rerenderAllComponents();
    }
    
    // ========================================================================
    // FULL-TEXT SEARCH
    // ========================================================================
    
}

// ============================================================================
// GLOBÁLNÍ EVENT HANDLERS
// ============================================================================

/**
 * Globální funkce volané z HTML onclick handlers
 * Tyto funkce delegují na SearchManager instance
 */

let searchManager; // Global instance

async function initializeSearch() {
    searchManager = new ChronicleSearchManager();
    // The init method is now async
}

// HTML onclick handlers
function toggleBadge(badgeElement) {
    if (searchManager) {
        searchManager.handleBadgeClick(badgeElement);
    }
}


function removeBreadcrumb(removeButton, type, value) {
    if (searchManager) {
        searchManager.removeTextFilter(type, value);
    }
}

function clearAllFilters() {
    if (searchManager) {
        searchManager.clearAllFilters();
    }
}

// Removed: addYearFilter function as inputs are no longer used

function toggleYearPreset(badgeElement) {
    // This function is now handled by handleBadgeClick
    if (searchManager) {
        searchManager.handleBadgeClick(badgeElement);
    }
}

// ============================================================================
// INICIALIZACE
// ============================================================================

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ChronicleSearchManager
    };
}