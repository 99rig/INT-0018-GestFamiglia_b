/**
 * Script per gestire le select dinamiche delle sottocategorie nell'admin Django
 * Quando viene selezionata una categoria, carica le sottocategorie via AJAX
 */

(function($) {
    'use strict';

    // Cache per le sottocategorie già caricate
    const subcategoriesCache = {};

    // Funzione per caricare le sottocategorie via AJAX
    function loadSubcategories(categoryId, callback) {
        if (subcategoriesCache[categoryId]) {
            callback(subcategoriesCache[categoryId]);
            return;
        }

        const url = '/api/v1/admin/subcategories-by-category/';
        
        // Supporto sia per jQuery che fetch
        if (typeof $ !== 'undefined') {
            $.get(url, { category_id: categoryId })
                .done(function(data) {
                    subcategoriesCache[categoryId] = data.subcategories;
                    callback(data.subcategories);
                })
                .fail(function() {
                    console.error('Errore nel caricamento delle sottocategorie');
                    callback([]);
                });
        } else {
            // Fallback con fetch
            fetch(`${url}?category_id=${categoryId}`)
                .then(response => response.json())
                .then(data => {
                    subcategoriesCache[categoryId] = data.subcategories;
                    callback(data.subcategories);
                })
                .catch(error => {
                    console.error('Errore nel caricamento delle sottocategorie:', error);
                    callback([]);
                });
        }
    }

    // Funzione per aggiornare le opzioni della select sottocategoria
    function updateSubcategoryOptions(subcategorySelect, subcategories, selectedValue) {
        // Salva il valore attualmente selezionato
        const currentValue = selectedValue || subcategorySelect.value;
        
        // Pulisce le opzioni
        subcategorySelect.innerHTML = '<option value="">---------</option>';
        
        // Aggiunge le nuove opzioni
        subcategories.forEach(function(subcategory) {
            const option = document.createElement('option');
            option.value = subcategory.id;
            option.textContent = subcategory.name;
            
            // Ripristina la selezione se era già selezionata
            if (subcategory.id == currentValue) {
                option.selected = true;
            }
            
            subcategorySelect.appendChild(option);
        });
    }

    // Funzione per configurare una coppia categoria/sottocategoria
    function setupCategorySubcategoryPair(categorySelect, subcategorySelect) {
        if (!categorySelect || !subcategorySelect) {
            return;
        }

        // Salva il valore iniziale della sottocategoria
        const initialSubcategoryValue = subcategorySelect.value;

        function handleCategoryChange() {
            const categoryId = categorySelect.value;
            
            if (!categoryId) {
                // Se nessuna categoria è selezionata, svuota le sottocategorie
                subcategorySelect.innerHTML = '<option value="">---------</option>';
                return;
            }

            // Aggiunge un indicatore di caricamento
            subcategorySelect.innerHTML = '<option value="">Caricamento...</option>';
            subcategorySelect.disabled = true;

            // Carica le sottocategorie
            loadSubcategories(categoryId, function(subcategories) {
                updateSubcategoryOptions(subcategorySelect, subcategories);
                subcategorySelect.disabled = false;
            });
        }

        // Listener per cambiamenti nella categoria
        categorySelect.addEventListener('change', handleCategoryChange);

        // Carica le sottocategorie iniziali se c'è una categoria selezionata
        if (categorySelect.value) {
            loadSubcategories(categorySelect.value, function(subcategories) {
                updateSubcategoryOptions(subcategorySelect, subcategories, initialSubcategoryValue);
            });
        }
    }

    // Funzione per inizializzare tutte le select dinamiche nella pagina
    function initializeDynamicSubcategories() {
        // Form principale (add/change)
        const mainCategorySelect = document.getElementById('id_category');
        const mainSubcategorySelect = document.getElementById('id_subcategory');
        
        if (mainCategorySelect && mainSubcategorySelect) {
            setupCategorySubcategoryPair(mainCategorySelect, mainSubcategorySelect);
        }

        // Form inline (tabular e stacked)
        const inlineRows = document.querySelectorAll('.dynamic-form, .form-row, .inline-related');
        inlineRows.forEach(function(row) {
            const categorySelect = row.querySelector('select[name$="category"], select[id*="category"]');
            const subcategorySelect = row.querySelector('select[name$="subcategory"], select[id*="subcategory"]');
            
            if (categorySelect && subcategorySelect) {
                setupCategorySubcategoryPair(categorySelect, subcategorySelect);
            }
        });

        // Gestisce anche le quote inline se presenti
        const quoteRows = document.querySelectorAll('[id*="expensequota_set"], [class*="quota"]');
        quoteRows.forEach(function(row) {
            const categorySelect = row.querySelector('select[name*="category"]');
            const subcategorySelect = row.querySelector('select[name*="subcategory"]');
            
            if (categorySelect && subcategorySelect) {
                setupCategorySubcategoryPair(categorySelect, subcategorySelect);
            }
        });
    }

    // Inizializza al caricamento del DOM
    function initialize() {
        initializeDynamicSubcategories();
        
        // Re-inizializza quando vengono aggiunti nuovi form inline
        document.addEventListener('DOMNodeInserted', function(e) {
            if (e.target.nodeType === 1) { // Solo nodi elemento
                const target = e.target;
                if (target.matches && (target.matches('.dynamic-form') || target.matches('.form-row'))) {
                    setTimeout(initializeDynamicSubcategories, 100);
                }
            }
        });
    }

    // Supporta sia jQuery che DOM ready nativo
    if (typeof $ !== 'undefined') {
        $(document).ready(function() {
            initialize();
            
            // Gestisce l'aggiunta di nuovi form inline con jQuery
            $(document).on('formset:added', function(event, $row) {
                setTimeout(initializeDynamicSubcategories, 100);
            });
        });
    } else {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initialize);
        } else {
            initialize();
        }
    }

})(typeof django !== 'undefined' ? django.jQuery : (typeof jQuery !== 'undefined' ? jQuery : undefined));