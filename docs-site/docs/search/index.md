---
title: Pokročilé vyhledávání
---

# Pokročilé vyhledávání

<link rel="stylesheet" href="style.css">
<script src="search.js" defer></script>

<div class="md-container">
    <div class="search-header">
        <h1>Aktivní filtry</h1>
        
        <div class="search-breadcrumbs">
            <div class="breadcrumb-filters">
                <!-- Active filters will be rendered here -->
            </div>
            <button class="breadcrumb-clear-all" onclick="clearAllFilters()">Vymazat vše</button>
        </div>
    </div>
    
    <div class="search-filters">
        <div class="tab-container">
            <div class="tab-list" role="tablist">
                <button class="tab-button active" role="tab" aria-selected="true" aria-controls="tab-panel-years" data-filter="years">
                    📅 Roky
                </button>
                <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-panel-houses" data-filter="houses">
                    🏠 Čísla popisná
                </button>
                <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-panel-names" data-filter="names">
                    👤 Jména
                </button>
                <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-panel-keywords" data-filter="keywords">
                    🔍 Klíčová slova
                </button>
            </div>
            <div class="tab-panels">
                <!-- Years Panel -->
                <div class="tab-panel active" role="tabpanel" id="tab-panel-years">
                    <div class="badge-container">
                        <!-- Year preset badges will be rendered here -->
                    </div>
                </div>
                <!-- House Numbers Panel -->
                <div class="tab-panel" role="tabpanel" id="tab-panel-houses">
                    <input type="text" class="filter-input" placeholder="Hledat čísla popisná...">
                    <div class="badge-container"></div>
                </div>
                <!-- Names Panel -->
                <div class="tab-panel" role="tabpanel" id="tab-panel-names">
                    <input type="text" class="filter-input" placeholder="Hledat jména...">
                    <div class="badge-container"></div>
                </div>
                <!-- Keywords Panel -->
                <div class="tab-panel" role="tabpanel" id="tab-panel-keywords">
                    <div class="badge-container">
                        <!-- Available keyword badges will be rendered here -->
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="search-results">
        <div class="chapter-group">
            <h3 class="chapter-title">Úvod</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_001/" class="content-dot intensity-3" data-tooltip="Úvod" data-original-intensity="intensity-3"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">Základní informace o obci</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_002/" class="content-dot intensity-4" data-tooltip="Základní informace o obci" data-original-intensity="intensity-4"></a>
                <a href="/kronika/chapters/chapter_003/" class="content-dot intensity-3" data-tooltip="Obec Stará Ves" data-original-intensity="intensity-3"></a>
                <a href="/kronika/chapters/chapter_004/" class="content-dot intensity-1" data-tooltip="Památnosti a významná místa" data-original-intensity="intensity-1"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">Rané dějiny (do 1700)</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_005/" class="content-dot intensity-5" data-tooltip="Rané dějiny (do 1700)" data-original-intensity="intensity-5"></a>
                <a href="/kronika/chapters/chapter_006/" class="content-dot intensity-3" data-tooltip="Vrchnost do roku 1620" data-original-intensity="intensity-3"></a>
                <a href="/kronika/chapters/chapter_007/" class="content-dot intensity-2" data-tooltip="Historie Hradu Navarova" data-original-intensity="intensity-2"></a>
                <a href="/kronika/chapters/chapter_008/" class="content-dot intensity-4" data-tooltip="Doba od r. 1620 do r. 1634" data-original-intensity="intensity-4"></a>
                <a href="/kronika/chapters/chapter_009/" class="content-dot intensity-3" data-tooltip="Doba od roku 1634" data-original-intensity="intensity-3"></a>
                <a href="/kronika/chapters/chapter_010/" class="content-dot intensity-2" data-tooltip="Protireformace od roku 1648" data-original-intensity="intensity-2"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">18. a 19. století (1700–1914)</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_011/" class="content-dot intensity-2" data-tooltip="18. a 19. století (1700–1914)" data-original-intensity="intensity-2"></a>
                <a href="/kronika/chapters/chapter_012/" class="content-dot intensity-5" data-tooltip="Od roku 1700" data-original-intensity="intensity-5"></a>
                <a href="/kronika/chapters/chapter_013/" class="content-dot intensity-3" data-tooltip="Od roku 1800" data-original-intensity="intensity-3"></a>
                <a href="/kronika/chapters/chapter_014/" class="content-dot intensity-4" data-tooltip="Sedláci v Staré Vsi roku 1842" data-original-intensity="intensity-4"></a>
                <a href="/kronika/chapters/chapter_015/" class="content-dot intensity-1" data-tooltip="Roku 1912" data-original-intensity="intensity-1"></a>
                <a href="/kronika/chapters/chapter_016/" class="content-dot intensity-2" data-tooltip="Některá památnější úmrtí od roku 1881" data-original-intensity="intensity-2"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">První světová válka (1914–1918)</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_017/" class="content-dot intensity-5" data-tooltip="První světová válka (1914–1918)" data-original-intensity="intensity-5"></a>
                <a href="/kronika/chapters/chapter_018/" class="content-dot intensity-4" data-tooltip="Válka světová" data-original-intensity="intensity-4"></a>
                <a href="/kronika/chapters/chapter_019/" class="content-dot intensity-3" data-tooltip="Průběh války (1915–1918)" data-original-intensity="intensity-3"></a>
                <a href="/kronika/chapters/chapter_020/" class="content-dot intensity-2" data-tooltip="Oběti Války ze Staré Vsi r. 1914 – 1918" data-original-intensity="intensity-2"></a>
                <a href="/kronika/chapters/chapter_021/" class="content-dot intensity-3" data-tooltip="Legionáři ze Staré Vsi" data-original-intensity="intensity-3"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">Meziválečné období (1918–1938)</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_022/" class="content-dot intensity-3" data-tooltip="Meziválečné období (1918–1938))" data-original-intensity="intensity-3"></a>
                <a href="/kronika/chapters/chapter_023/" class="content-dot intensity-4" data-tooltip="Vznik Československé republiky (1918–1922)" data-original-intensity="intensity-4"></a>
                <a href="/kronika/chapters/chapter_024/" class="content-dot disabled" data-tooltip="Roky 1923–1927" data-original-intensity="disabled"></a>
                <a href="/kronika/chapters/chapter_025/" class="content-dot intensity-5" data-tooltip="Roky 1928–1934" data-original-intensity="intensity-5"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">Válečné a poválečné období (1935–1953)</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_026/" class="content-dot intensity-5" data-tooltip="Válečné a poválečné období (1935–1953)" data-original-intensity="intensity-5"></a>
                <a href="/kronika/chapters/chapter_027/" class="content-dot intensity-4" data-tooltip="Předválečné roky (1935–1938)" data-original-intensity="intensity-4"></a>
                <a href="/kronika/chapters/chapter_028/" class="content-dot intensity-3" data-tooltip="Druhá světová válka (1939–1945)" data-original-intensity="intensity-3"></a>
                <a href="/kronika/chapters/chapter_029/" class="content-dot intensity-2" data-tooltip="Poválečné roky (1946–1953)" data-original-intensity="intensity-2"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">Novější dějiny (1979–1991)</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_030/" class="content-dot intensity-2" data-tooltip="Novější dějiny (1979–1991)" data-original-intensity="intensity-2"></a>
                <a href="/kronika/chapters/chapter_031/" class="content-dot disabled" data-tooltip="Osmdesátá léta (1979–1989)" data-original-intensity="disabled"></a>
                <a href="/kronika/chapters/chapter_032/" class="content-dot intensity-3" data-tooltip="Sametová revoluce a její následky (1989–1991)" data-original-intensity="intensity-3"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">Dějiny školy staroveské</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_033/" class="content-dot intensity-4" data-tooltip="Dějiny školy staroveské" data-original-intensity="intensity-4"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">Historie domů a jejich obyvatel</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_034/" class="content-dot intensity-5" data-tooltip="Historie domů a jejich obyvatel" data-original-intensity="intensity-5"></a>
                <a href="/kronika/chapters/chapter_035/" class="content-dot intensity-4" data-tooltip="Domy č. 1–20" data-original-intensity="intensity-4"></a>
                <a href="/kronika/chapters/chapter_036/" class="content-dot intensity-3" data-tooltip="Domy č. 21–40" data-original-intensity="intensity-3"></a>
                <a href="/kronika/chapters/chapter_037/" class="content-dot intensity-2" data-tooltip="Domy č. 41–57" data-original-intensity="intensity-2"></a>
                <a href="/kronika/chapters/chapter_038/" class="content-dot disabled" data-tooltip="Rody a genealogie" data-original-intensity="disabled"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">Okolní obce a regiony</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_039/" class="content-dot intensity-3" data-tooltip="Okolní obce a regiony" data-original-intensity="intensity-3"></a>
                <a href="/kronika/chapters/chapter_040/" class="content-dot intensity-2" data-tooltip="Z dějin městečka Vysokého" data-original-intensity="intensity-2"></a>
                <a href="/kronika/chapters/chapter_041/" class="content-dot intensity-1" data-tooltip="Patricijská jména z okolí" data-original-intensity="intensity-1"></a>
                <a href="/kronika/chapters/chapter_042/" class="content-dot disabled" data-tooltip="Z Dějin národa českého" data-original-intensity="disabled"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">Přílohy</h3>
            <div class="dots-container">
                <a href="/kronika/chapters/chapter_043/" class="content-dot disabled" data-tooltip="Přílohy" data-original-intensity="disabled"></a>
                <a href="/kronika/chapters/chapter_044/" class="content-dot disabled" data-tooltip="Regista" data-original-intensity="disabled"></a>
                <a href="/kronika/chapters/chapter_045/" class="content-dot disabled" data-tooltip="Různé" data-original-intensity="disabled"></a>
            </div>
        </div>
        <div class="chapter-group">
            <h3 class="chapter-title">Indexy</h3>
            <div class="dots-container">
                <a href="/kronika/indexes/address_number/" class="content-dot intensity-5" data-tooltip="Čísla popisná" data-original-intensity="intensity-5"></a>
                <a href="/kronika/indexes/event/" class="content-dot intensity-4" data-tooltip="Klíčová slova" data-original-intensity="intensity-4"></a>
                <a href="/kronika/indexes/name/" class="content-dot intensity-5" data-tooltip="Jména" data-original-intensity="intensity-5"></a>
                <a href="/kronika/indexes/year/" class="content-dot intensity-4" data-tooltip="Roky" data-original-intensity="intensity-4"></a>
            </div>
        </div>
    </div>