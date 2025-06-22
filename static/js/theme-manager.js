/* filepath: c:\Users\d.tolkunov\CodeRepository\AnalyticsRepo\discount-service\static\js\theme-manager.js */
/**
 * Менеджер тем для discount-service
 */
class ThemeManager {
    constructor() {
        this.STORAGE_KEY = 'gh_theme_preference';
        this.COOKIE_KEY = 'gh_theme';
        this.DARK_THEME_CLASS = 'dark-theme';
        this.themes = {
            light: 'light',
            dark: 'dark'
        };
        
        // ИСПОЛЬЗУЕМ СУЩЕСТВУЮЩИЕ ЛОГОТИПЫ
        this.logos = {
            light: '/discount-system/static/img/logo-dark.svg',
            dark: '/discount-system/static/img/logo-light.svg'
        };
        
        this.init();
    }

    init() {
        this.applyThemeImmediately();
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeComponents());
        } else {
            this.initializeComponents();
        }

        window.addEventListener('storage', (e) => {
            if (e.key === this.STORAGE_KEY && e.newValue !== e.oldValue) {
                this.applyTheme(e.newValue || this.themes.light, false);
            }
        });
    }

    setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    }

    getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    applyThemeImmediately() {
        const cookieTheme = this.getCookie(this.COOKIE_KEY);
        const savedTheme = cookieTheme || localStorage.getItem(this.STORAGE_KEY) || this.themes.light;
        
        if (savedTheme === this.themes.dark) {
            document.documentElement.classList.add(this.DARK_THEME_CLASS);
            // Проверяем, что body существует
            if (document.body) {
                document.body.classList.add(this.DARK_THEME_CLASS);
            }
        }
        
        if (cookieTheme && cookieTheme !== localStorage.getItem(this.STORAGE_KEY)) {
            localStorage.setItem(this.STORAGE_KEY, cookieTheme);
        }
    }

    async initializeComponents() {
        this.initParticles();
        this.bindEvents();
        
        // Отладка - проверяем наличие логотипов
        console.log('Logo light element:', document.getElementById('logo-light'));
        console.log('Logo dark element:', document.getElementById('logo-dark'));
        console.log('Logo container:', document.querySelector('.logo-container'));
        
        const currentTheme = this.getCurrentTheme();
        this.updateLogos(currentTheme);
        this.updateSwitcherUI(currentTheme);
        
        console.log('ThemeManager initialized with theme:', currentTheme);
    }

    initParticles() {
        if (typeof particlesJS === 'undefined') {
            console.warn('particles.js not loaded');
            return;
        }

        particlesJS('particles-js', {
            "particles": { 
                "number": { 
                    "value": 50, 
                    "density": { 
                        "enable": true, 
                        "value_area": 800 
                    } 
                }, 
                "color": { 
                    "value": "#c4a668" 
                }, 
                "shape": { 
                    "type": "polygon", 
                    "stroke": { 
                        "width": 1, 
                        "color": "#c4a668" 
                    }, 
                    "polygon": { 
                        "nb_sides": 6 
                    } 
                }, 
                "opacity": { 
                    "value": 0.2, 
                    "random": true, 
                    "anim": { 
                        "enable": true, 
                        "speed": 0.5, 
                        "opacity_min": 0.05, 
                        "sync": false 
                    } 
                }, 
                "size": { 
                    "value": 4, 
                    "random": true 
                }, 
                "line_linked": { 
                    "enable": true, 
                    "distance": 180, 
                    "color": "#c4a668", 
                    "opacity": 0.15, 
                    "width": 1 
                }, 
                "move": { 
                    "enable": true, 
                    "speed": 0.8, 
                    "direction": "none", 
                    "random": true, 
                    "straight": false, 
                    "out_mode": "out" 
                } 
            }, 
            "interactivity": { 
                "detect_on": "canvas", 
                "events": { 
                    "onhover": { 
                        "enable": true, 
                        "mode": "bubble" 
                    } 
                }, 
                "modes": { 
                    "bubble": { 
                        "distance": 200, 
                        "size": 6, 
                        "duration": 2, 
                        "opacity": 0.6 
                    } 
                } 
            }, 
            "retina_detect": true
        });
    }

    setupLogos() {
        const logoContainer = document.querySelector('.logo-container');
        if (!logoContainer) return;

        // Создаем оба логотипа если их нет
        if (!document.getElementById('logo-light')) {
            const lightLogo = document.createElement('img');
            lightLogo.id = 'logo-light';
            lightLogo.className = 'logo';
            lightLogo.src = this.logos.light;
            lightLogo.alt = 'Golden House Logo';
            logoContainer.insertBefore(lightLogo, logoContainer.firstChild);
        }

        if (!document.getElementById('logo-dark')) {
            const darkLogo = document.createElement('img');
            darkLogo.id = 'logo-dark';
            darkLogo.className = 'logo hidden';
            darkLogo.src = this.logos.dark;
            darkLogo.alt = 'Golden House Logo';
            logoContainer.insertBefore(darkLogo, logoContainer.firstChild);
        }
    }

    createThemeSwitcher() {
        let switcher = document.getElementById('theme-switcher');
        
        if (!switcher) {
            switcher = document.createElement('button');
            switcher.id = 'theme-switcher';
            switcher.className = 'theme-switcher';
            switcher.innerHTML = '<i class="fas fa-moon"></i><span>Тёмная тема</span>';
            switcher.title = 'Переключить тему';
            
            const nav = document.querySelector('.nav');
            if (nav) {
                nav.appendChild(switcher);
            }
        }

        this.themeSwitcher = switcher;
    }

    bindEvents() {
        const themeSwitcher = document.getElementById('theme-switcher');
        
        if (themeSwitcher) {
            themeSwitcher.addEventListener('click', () => {
                this.toggleTheme();
            });
            console.log('Theme switcher bound');
        } else {
            console.warn('Theme switcher button not found');
        }
    }

    getCurrentTheme() {
        const cookieTheme = this.getCookie(this.COOKIE_KEY);
        return cookieTheme || localStorage.getItem(this.STORAGE_KEY) || this.themes.light;
    }

    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === this.themes.dark ? this.themes.light : this.themes.dark;
        this.setTheme(newTheme);
    }

    setTheme(theme) {
        this.applyTheme(theme, true);
    }

    async applyTheme(theme, updateStorage = true) {
        const htmlElement = document.documentElement;
        const bodyElement = document.body;

        if (theme === this.themes.light) {
            htmlElement.classList.remove(this.DARK_THEME_CLASS);
            if (bodyElement) {
                bodyElement.classList.remove(this.DARK_THEME_CLASS);
            }
        } else {
            htmlElement.classList.add(this.DARK_THEME_CLASS);
            if (bodyElement) {
                bodyElement.classList.add(this.DARK_THEME_CLASS);
            }
        }

        this.updateLogos(theme);

        if (updateStorage) {
            localStorage.setItem(this.STORAGE_KEY, theme);
            this.setCookie(this.COOKIE_KEY, theme, 365);
        }

        this.updateSwitcherUI(theme);
        console.log('Theme applied:', theme);
    }

    updateLogos(theme) {
        const lightLogo = document.getElementById('logo-light');
        const darkLogo = document.getElementById('logo-dark');

        console.log('Updating logos:', { 
            theme, 
            lightLogo: !!lightLogo, 
            darkLogo: !!darkLogo,
            lightLogoSrc: lightLogo?.src,
            darkLogoSrc: darkLogo?.src
        });

        if (lightLogo && darkLogo) {
            if (theme === this.themes.dark) {
                lightLogo.classList.add('hidden');
                darkLogo.classList.remove('hidden');
            } else {
                lightLogo.classList.remove('hidden');
                darkLogo.classList.add('hidden');
            }
            console.log(`Logos updated for ${theme} theme`);
        } else {
            console.warn('Logo elements not found:', { lightLogo: !!lightLogo, darkLogo: !!darkLogo });
        }
    }

    updateSwitcherUI(theme) {
        const themeSwitcher = document.getElementById('theme-switcher');
        
        if (!themeSwitcher) {
            console.warn('Theme switcher not found for UI update');
            return;
        }

        const iconElement = themeSwitcher.querySelector('i');
        const textElement = themeSwitcher.querySelector('span');
        
        if (theme === this.themes.dark) {
            if (iconElement) iconElement.className = 'fas fa-sun';
            if (textElement) textElement.textContent = 'Светлая тема';
            themeSwitcher.title = 'Переключить на светлую тему';
        } else {
            if (iconElement) iconElement.className = 'fas fa-moon';
            if (textElement) textElement.textContent = 'Тёмная тема';
            themeSwitcher.title = 'Переключить на тёмную тему';
        }
        console.log(`Switcher UI updated for ${theme} theme`);
    }

    static init() {
        if (!window.themeManager) {
            window.themeManager = new ThemeManager();
        }
        return window.themeManager;
    }
}

// Автоматическая инициализация
ThemeManager.init();