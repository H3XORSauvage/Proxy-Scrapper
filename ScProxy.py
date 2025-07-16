import requests
import os
import time
import threading
import concurrent.futures
import json
import re
import signal
import sys
import random
from datetime import datetime
from colorama import Fore, init
import fade
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

init(autoreset=True)

# Variable globale pour contrôler l'interruption
interrupt_flag = False

def signal_handler(signum, frame):
    """Gestionnaire de signal pour Ctrl+C."""
    global interrupt_flag
    print(Fore.YELLOW + "\n[INFO] Interruption demandée... Attendez la fin du batch en cours...")
    interrupt_flag = True

# Enregistrer le gestionnaire de signal
signal.signal(signal.SIGINT, signal_handler)

@dataclass
class Proxy:
    """Classe pour représenter un proxy avec ses métadonnées."""
    ip: str
    port: str
    proxy_type: str
    country: Optional[str] = None
    speed: Optional[float] = None
    last_checked: Optional[datetime] = None
    anonymity: Optional[str] = None

# Configuration des URLs de proxys
PROXY_URLS: Dict[str, List[str]] = {
    "SOCKS5": [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/refs/heads/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/socks5.txt"
    ],
    "SOCKS4": [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/refs/heads/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/socks4.txt"
    ],
    "HTTP": [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/refs/heads/main/proxies/http.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/http.txt"
    ],
    "HTTPS": [
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/refs/heads/main/proxies/https.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/https.txt"
    ]
}

def validate_proxy_format(proxy_str: str) -> Optional[Tuple[str, str]]:
    """Valide le format d'un proxy et retourne (ip, port)."""
    # Patterns pour différents formats de proxy
    patterns = [
        r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$',  # IP:PORT
        r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5}):(\w+):(\w+)$',  # IP:PORT:USER:PASS
    ]
    
    for pattern in patterns:
        match = re.match(pattern, proxy_str.strip())
        if match:
            ip = match.group(1)
            port = match.group(2)
            
            # Validation supplémentaire de l'IP et du port
            if not is_valid_ip(ip) or not is_valid_port(port):
                return None
                
            return ip, port
    return None

def is_valid_ip(ip: str) -> bool:
    """Valide une adresse IP."""
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit() or not (0 <= int(part) <= 255):
                return False
        return True
    except:
        return False

def is_valid_port(port: str) -> bool:
    """Valide un numéro de port."""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except:
        return False

def test_proxy(proxy: Proxy, timeout: int = 5) -> bool:
    """Teste si un proxy fonctionne avec un timeout plus court."""
    global interrupt_flag
    if interrupt_flag:
        return False
        
    try:
        proxy_dict = {
            'http': f'{proxy.proxy_type.lower()}://{proxy.ip}:{proxy.port}',
            'https': f'{proxy.proxy_type.lower()}://{proxy.ip}:{proxy.port}'
        }
        
        # Test avec une requête simple et timeout court
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxy_dict,
            timeout=timeout
        )
        return response.status_code == 200
    except:
        return False

def test_proxy_speed(proxy: Proxy, timeout: int = 10) -> Optional[float]:
    """Teste la vitesse d'un proxy et retourne le temps de réponse en secondes."""
    try:
        proxy_dict = {
            'http': f'{proxy.proxy_type.lower()}://{proxy.ip}:{proxy.port}',
            'https': f'{proxy.proxy_type.lower()}://{proxy.ip}:{proxy.port}'
        }
        
        start_time = time.time()
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxy_dict,
            timeout=timeout
        )
        end_time = time.time()
        
        if response.status_code == 200:
            return end_time - start_time
        return None
    except:
        return None

def get_proxy_country(proxy: Proxy) -> Optional[str]:
    """Tente de déterminer le pays du proxy."""
    try:
        proxy_dict = {
            'http': f'{proxy.proxy_type.lower()}://{proxy.ip}:{proxy.port}',
            'https': f'{proxy.proxy_type.lower()}://{proxy.ip}:{proxy.port}'
        }
        
        response = requests.get(
            'http://ip-api.com/json',
            proxies=proxy_dict,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('countryCode', 'Unknown')
        return None
    except:
        return None

def validate_proxies_batch(proxies: List[Proxy], batch_size: int = 100, max_workers: int = 20) -> List[Proxy]:
    """Valide les proxys par batch pour éviter la surcharge."""
    global interrupt_flag
    interrupt_flag = False
    working_proxies = []
    total_proxies = len(proxies)
    
    print(Fore.CYAN + f"[INFO] Validation de {total_proxies} proxys par batch de {batch_size}...")
    print(Fore.YELLOW + "[INFO] Appuyez sur Ctrl+C pour interrompre la validation")
    
    for i in range(0, total_proxies, batch_size):
        if interrupt_flag:
            print(Fore.YELLOW + "\n[INFO] Validation interrompue par l'utilisateur")
            break
            
        batch = proxies[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_proxies + batch_size - 1) // batch_size
        
        print(Fore.YELLOW + f"[INFO] Batch {batch_num}/{total_batches} ({len(batch)} proxys)...")
        
        # Validation du batch en parallèle
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in batch}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_proxy):
                if interrupt_flag:
                    break
                    
                proxy = future_to_proxy[future]
                completed += 1
                
                try:
                    if future.result():
                        working_proxies.append(proxy)
                except Exception:
                    continue
                
                # Affichage de progression
                if completed % 10 == 0 or completed == len(batch):
                    progress = (completed / len(batch)) * 100
                    working_count = len([p for p in working_proxies if p in batch])
                    print(Fore.GREEN + f"  Progression: {progress:.1f}% - {working_count} fonctionnels")
        
        if interrupt_flag:
            break
            
        # Pause courte entre les batchs pour éviter la surcharge
        time.sleep(0.5)
    
    return working_proxies

def test_proxies_speed(proxies: List[Proxy], max_workers: int = 10) -> List[Proxy]:
    """Teste la vitesse de tous les proxys et les trie par vitesse."""
    print(Fore.CYAN + f"[INFO] Test de vitesse pour {len(proxies)} proxys...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {executor.submit(test_proxy_speed, proxy): proxy for proxy in proxies}
        
        for future in concurrent.futures.as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                speed = future.result()
                if speed is not None:
                    proxy.speed = speed
            except Exception:
                continue
    
    # Trier par vitesse (plus rapide en premier)
    fast_proxies = [p for p in proxies if p.speed is not None]
    fast_proxies.sort(key=lambda x: x.speed or 999.0)
    
    print(Fore.GREEN + f"[INFO] {len(fast_proxies)} proxys testés pour la vitesse")
    return fast_proxies

def filter_proxies_by_country(proxies: List[Proxy], country_codes: List[str]) -> List[Proxy]:
    """Filtre les proxys par pays."""
    print(Fore.CYAN + f"[INFO] Filtrage par pays: {', '.join(country_codes)}")
    
    filtered_proxies = []
    for proxy in proxies:
        country = get_proxy_country(proxy)
        if country and country.upper() in [c.upper() for c in country_codes]:
            proxy.country = country
            filtered_proxies.append(proxy)
    
    print(Fore.GREEN + f"[INFO] {len(filtered_proxies)} proxys trouvés pour les pays spécifiés")
    return filtered_proxies

def create_proxy_rotator(proxies: List[Proxy]):
    """Crée un rotateur de proxys qui change automatiquement."""
    proxy_list = proxies.copy()
    random.shuffle(proxy_list)
    current_index = 0
    
    def get_next_proxy():
        nonlocal current_index
        if not proxy_list:
            return None
        
        proxy = proxy_list[current_index]
        current_index = (current_index + 1) % len(proxy_list)
        return proxy
    
    return get_next_proxy

def scrape_proxies(proxy_type: str, validate: bool = False, max_workers: int = 10) -> List[Proxy]:
    """Scrape des proxys avec validation optionnelle optimisée."""
    if proxy_type not in PROXY_URLS:
        print(Fore.RED + "Type de proxy invalide.")
        return []

    print(Fore.CYAN + f"[INFO] Début du scraping des proxys {proxy_type}...")
    all_proxies: List[Proxy] = []
    
    # Scraping parallèle des URLs
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(scrape_single_url, url, proxy_type): url 
            for url in PROXY_URLS[proxy_type]
        }
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                proxies_from_url = future.result()
                all_proxies.extend(proxies_from_url)
                print(Fore.GREEN + f"[+] {len(proxies_from_url)} proxys récupérés depuis {url}")
            except Exception as e:
                print(Fore.YELLOW + f"[Erreur] Impossible de scraper depuis {url}: {e}")

    # Suppression des doublons
    unique_proxies = remove_duplicates(all_proxies)
    print(Fore.CYAN + f"[INFO] {len(unique_proxies)} proxys uniques trouvés")

    # Validation optionnelle avec gestion des gros volumes
    if validate and unique_proxies:
        if len(unique_proxies) > 1000:
            print(Fore.YELLOW + "[INFO] Gros volume détecté, utilisation de la validation par batch...")
            working_proxies = validate_proxies_batch(unique_proxies)
        else:
            print(Fore.YELLOW + "[INFO] Validation des proxys en cours...")
            working_proxies = validate_proxies_parallel(unique_proxies, max_workers)
        
        print(Fore.GREEN + f"[INFO] {len(working_proxies)} proxys fonctionnels trouvés")
        return working_proxies
    
    return unique_proxies

def scrape_single_url(url: str, proxy_type: str) -> List[Proxy]:
    """Scrape les proxys d'une URL spécifique."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        proxies = []
        for line in response.text.splitlines():
            line = line.strip()
            if not line:
                continue
                
            proxy_info = validate_proxy_format(line)
            if proxy_info:
                ip, port = proxy_info
                proxies.append(Proxy(ip=ip, port=port, proxy_type=proxy_type))
        
        return proxies
    except Exception as e:
        raise e

def remove_duplicates(proxies: List[Proxy]) -> List[Proxy]:
    """Supprime les proxys en double basés sur IP:PORT."""
    seen = set()
    unique_proxies = []
    
    for proxy in proxies:
        proxy_key = f"{proxy.ip}:{proxy.port}"
        if proxy_key not in seen:
            seen.add(proxy_key)
            unique_proxies.append(proxy)
    
    return unique_proxies

def validate_proxies_parallel(proxies: List[Proxy], max_workers: int = 10) -> List[Proxy]:
    """Valide les proxys en parallèle (pour petits volumes)."""
    global interrupt_flag
    interrupt_flag = False
    working_proxies = []
    
    print(Fore.YELLOW + "[INFO] Appuyez sur Ctrl+C pour interrompre la validation")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        
        for future in concurrent.futures.as_completed(future_to_proxy):
            if interrupt_flag:
                print(Fore.YELLOW + "\n[INFO] Validation interrompue par l'utilisateur")
                break
                
            proxy = future_to_proxy[future]
            try:
                if future.result():
                    working_proxies.append(proxy)
            except Exception:
                continue
    
    return working_proxies

def save_proxies_to_file(filename: str, proxies: List[Proxy], format_type: str = "simple") -> None:
    """Sauvegarde les proxys dans un fichier avec différents formats."""
    if format_type == "simple":
        with open(filename, "w", encoding="utf-8") as file:
            for proxy in proxies:
                file.write(f"{proxy.ip}:{proxy.port}\n")
    elif format_type == "detailed":
        with open(filename, "w", encoding="utf-8") as file:
            file.write("IP:PORT:TYPE:COUNTRY:SPEED:LAST_CHECKED\n")
            for proxy in proxies:
                country = proxy.country or "Unknown"
                speed = proxy.speed or "Unknown"
                last_checked = proxy.last_checked.isoformat() if proxy.last_checked else "Unknown"
                file.write(f"{proxy.ip}:{proxy.port}:{proxy.proxy_type}:{country}:{speed}:{last_checked}\n")
    elif format_type == "json":
        proxy_list = []
        for proxy in proxies:
            proxy_dict = {
                "ip": proxy.ip,
                "port": proxy.port,
                "type": proxy.proxy_type,
                "country": proxy.country,
                "speed": proxy.speed,
                "last_checked": proxy.last_checked.isoformat() if proxy.last_checked else None
            }
            proxy_list.append(proxy_dict)
        
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(proxy_list, file, indent=2, default=str)
    
    print(Fore.GREEN + f"[+] {len(proxies)} proxys enregistrés dans '{filename}' (format: {format_type})")

def show_info() -> None:
    """Affiche les informations détaillées sur les URLs disponibles."""
    print(Fore.CYAN + "\n[INFO] Détails des URLs par type de proxy :")
    for proxy_type, url_list in PROXY_URLS.items():
        print(Fore.YELLOW + f"\n{proxy_type}:")
        for i, url in enumerate(url_list, 1):
            print(Fore.GREEN + f"  {i}. {url}")

def clear_screen() -> None:
    """Efface l'écran selon le système d'exploitation."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner() -> None:
    """Affiche la bannière personnalisée avec effet fade."""
    banner = """
 _____                                                               _____ 
( ___ )                                                             ( ___ )
 |   |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|   | 
 |   | ███████╗ ██████╗   ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗ |   | 
 |   | ██╔════╝██╔════╝   ██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝ |   | 
 |   | ███████╗██║        ██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝  |   | 
 |   | ╚════██║██║        ██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝   |   | 
 |   | ███████║╚██████╗██╗██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║    |   | 
 |   | ╚══════╝ ╚═════╝╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝    |   | 
 |___|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|___| 
(_____)                                                             (_____)
"""
    faded_text = fade.purplepink(banner) 
    print(faded_text)

def prompt_to_continue() -> None:
    """Affiche un message et attend l'entrée de l'utilisateur pour continuer."""
    input(Fore.YELLOW + "\nAppuyez sur une touche pour revenir au menu...")

def main() -> None:
    """Fonction principale avec menu amélioré."""
    # Constantes pour les choix du menu
    CHOICE_EXIT = "1"
    CHOICE_SCRAPE_SOCKS5 = "2"
    CHOICE_SCRAPE_SOCKS4 = "3"
    CHOICE_SCRAPE_HTTP = "4"
    CHOICE_SCRAPE_HTTPS = "5"
    CHOICE_SCRAPE_ALL = "6"
    CHOICE_VALIDATE_PROXIES = "7"
    CHOICE_FAST_VALIDATION = "8"
    CHOICE_SHOW_INFO = "9"
    CHOICE_TEST_SPEED = "10"
    CHOICE_FILTER_COUNTRY = "11"
    CHOICE_CREATE_ROTATOR = "12"

    # Mapping des choix vers les types de proxy
    proxy_scrape_options = {
        CHOICE_SCRAPE_SOCKS5: "SOCKS5",
        CHOICE_SCRAPE_SOCKS4: "SOCKS4",
        CHOICE_SCRAPE_HTTP: "HTTP",
        CHOICE_SCRAPE_HTTPS: "HTTPS",
    }

    while True:
        clear_screen()
        display_banner() 
        print(Fore.MAGENTA + f"{CHOICE_EXIT} - Quitter le script")
        print(Fore.CYAN + f"\n{CHOICE_SCRAPE_SOCKS5} - Scraper des proxys SOCKS5")
        print(Fore.CYAN + f"{CHOICE_SCRAPE_SOCKS4} - Scraper des proxys SOCKS4")
        print(Fore.CYAN + f"{CHOICE_SCRAPE_HTTP} - Scraper des proxys HTTP")
        print(Fore.CYAN + f"{CHOICE_SCRAPE_HTTPS} - Scraper des proxys HTTPS")
        print(Fore.CYAN + f"{CHOICE_SCRAPE_ALL} - Scraper tous les types de proxys")
        print(Fore.CYAN + f"{CHOICE_VALIDATE_PROXIES} - Valider des proxys existants")
        print(Fore.CYAN + f"{CHOICE_FAST_VALIDATION} - Validation rapide (sans scraping)")
        print(Fore.CYAN + f"{CHOICE_SHOW_INFO} - Afficher les informations sur les URLs disponibles")
        print(Fore.GREEN + f"\n{CHOICE_TEST_SPEED} - Tester la vitesse des proxys")
        print(Fore.GREEN + f"{CHOICE_FILTER_COUNTRY} - Filtrer par pays")
        print(Fore.GREEN + f"{CHOICE_CREATE_ROTATOR} - Créer un rotateur de proxys")
        
        choix = input(Fore.YELLOW + f"Choisissez une option ({CHOICE_EXIT} à {CHOICE_CREATE_ROTATOR}) : ")

        if choix == CHOICE_EXIT:
            clear_screen()
            print(Fore.RED + "Fermeture du script...")
            break

        elif choix == CHOICE_SHOW_INFO:
            show_info()
            prompt_to_continue()

        elif choix == CHOICE_SCRAPE_ALL:
            print(Fore.GREEN + "[*] Scraping de tous les types de proxys en cours...")
            all_proxies = []
            for proxy_type in PROXY_URLS.keys():
                print(Fore.CYAN + f"[INFO] Scraping {proxy_type}...")
                proxies = scrape_proxies(proxy_type, validate=False)
                all_proxies.extend(proxies)
            
            if all_proxies:
                filename = f"all_proxies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                save_proxies_to_file(filename, all_proxies)
            else:
                print(Fore.RED + "Aucun proxy trouvé.")
            prompt_to_continue()

        elif choix == CHOICE_VALIDATE_PROXIES:
            filename = input(Fore.YELLOW + "Entrez le nom du fichier de proxys à valider : ")
            try:
                with open(filename, 'r') as file:
                    proxy_lines = file.readlines()
                
                proxies = []
                for line in proxy_lines:
                    proxy_info = validate_proxy_format(line.strip())
                    if proxy_info:
                        ip, port = proxy_info
                        proxies.append(Proxy(ip=ip, port=port, proxy_type="HTTP"))
                
                if proxies:
                    print(Fore.GREEN + f"[*] Validation de {len(proxies)} proxys...")
                    if len(proxies) > 1000:
                        print(Fore.YELLOW + "[INFO] Gros volume détecté, utilisation de la validation par batch...")
                        working_proxies = validate_proxies_batch(proxies)
                    else:
                        working_proxies = validate_proxies_parallel(proxies)
                    
                    if working_proxies:
                        output_filename = f"validated_{filename}"
                        save_proxies_to_file(output_filename, working_proxies)
                    else:
                        print(Fore.RED + "Aucun proxy fonctionnel trouvé.")
                else:
                    print(Fore.RED + "Aucun proxy valide trouvé dans le fichier.")
            except FileNotFoundError:
                print(Fore.RED + f"Fichier '{filename}' non trouvé.")
            except Exception as e:
                print(Fore.RED + f"Erreur lors de la validation : {e}")
            prompt_to_continue()

        elif choix == CHOICE_FAST_VALIDATION:
            print(Fore.GREEN + "[*] Mode validation rapide activé...")
            filename = input(Fore.YELLOW + "Entrez le nom du fichier de proxys à valider : ")
            try:
                with open(filename, 'r') as file:
                    proxy_lines = file.readlines()
                
                proxies = []
                for line in proxy_lines:
                    proxy_info = validate_proxy_format(line.strip())
                    if proxy_info:
                        ip, port = proxy_info
                        proxies.append(Proxy(ip=ip, port=port, proxy_type="HTTP"))
                
                if proxies:
                    print(Fore.GREEN + f"[*] Validation rapide de {len(proxies)} proxys (timeout: 3s)...")
                    # Validation avec timeout très court
                    working_proxies = validate_proxies_batch(proxies, batch_size=200, max_workers=30)
                    
                    if working_proxies:
                        output_filename = f"fast_validated_{filename}"
                        save_proxies_to_file(output_filename, working_proxies)
                    else:
                        print(Fore.RED + "Aucun proxy fonctionnel trouvé.")
                else:
                    print(Fore.RED + "Aucun proxy valide trouvé dans le fichier.")
            except FileNotFoundError:
                print(Fore.RED + f"Fichier '{filename}' non trouvé.")
            except Exception as e:
                print(Fore.RED + f"Erreur lors de la validation : {e}")
            prompt_to_continue()

        elif choix == CHOICE_TEST_SPEED:
            filename = input(Fore.YELLOW + "Entrez le nom du fichier de proxys à tester : ")
            try:
                with open(filename, 'r') as file:
                    proxy_lines = file.readlines()
                
                proxies = []
                for line in proxy_lines:
                    proxy_info = validate_proxy_format(line.strip())
                    if proxy_info:
                        ip, port = proxy_info
                        proxies.append(Proxy(ip=ip, port=port, proxy_type="HTTP"))
                
                if proxies:
                    print(Fore.GREEN + f"[*] Test de vitesse pour {len(proxies)} proxys...")
                    fast_proxies = test_proxies_speed(proxies)
                    
                    if fast_proxies:
                        output_filename = f"speed_tested_{filename}"
                        save_proxies_to_file(output_filename, fast_proxies, "detailed")
                        
                        # Afficher les 10 plus rapides
                        print(Fore.CYAN + "\n[INFO] Top 10 des proxys les plus rapides :")
                        for i, proxy in enumerate(fast_proxies[:10], 1):
                            print(Fore.GREEN + f"  {i}. {proxy.ip}:{proxy.port} - {proxy.speed:.2f}s")
                    else:
                        print(Fore.RED + "Aucun proxy testé avec succès.")
                else:
                    print(Fore.RED + "Aucun proxy valide trouvé dans le fichier.")
            except FileNotFoundError:
                print(Fore.RED + f"Fichier '{filename}' non trouvé.")
            except Exception as e:
                print(Fore.RED + f"Erreur lors du test de vitesse : {e}")
            prompt_to_continue()

        elif choix == CHOICE_FILTER_COUNTRY:
            filename = input(Fore.YELLOW + "Entrez le nom du fichier de proxys : ")
            countries = input(Fore.YELLOW + "Entrez les codes pays (séparés par des virgules, ex: US,FR,DE) : ").split(',')
            countries = [c.strip().upper() for c in countries]
            
            try:
                with open(filename, 'r') as file:
                    proxy_lines = file.readlines()
                
                proxies = []
                for line in proxy_lines:
                    proxy_info = validate_proxy_format(line.strip())
                    if proxy_info:
                        ip, port = proxy_info
                        proxies.append(Proxy(ip=ip, port=port, proxy_type="HTTP"))
                
                if proxies:
                    print(Fore.GREEN + f"[*] Filtrage par pays pour {len(proxies)} proxys...")
                    filtered_proxies = filter_proxies_by_country(proxies, countries)
                    
                    if filtered_proxies:
                        output_filename = f"filtered_{filename}"
                        save_proxies_to_file(output_filename, filtered_proxies, "detailed")
                    else:
                        print(Fore.RED + "Aucun proxy trouvé pour les pays spécifiés.")
                else:
                    print(Fore.RED + "Aucun proxy valide trouvé dans le fichier.")
            except FileNotFoundError:
                print(Fore.RED + f"Fichier '{filename}' non trouvé.")
            except Exception as e:
                print(Fore.RED + f"Erreur lors du filtrage : {e}")
            prompt_to_continue()

        elif choix == CHOICE_CREATE_ROTATOR:
            filename = input(Fore.YELLOW + "Entrez le nom du fichier de proxys : ")
            try:
                with open(filename, 'r') as file:
                    proxy_lines = file.readlines()
                
                proxies = []
                for line in proxy_lines:
                    proxy_info = validate_proxy_format(line.strip())
                    if proxy_info:
                        ip, port = proxy_info
                        proxies.append(Proxy(ip=ip, port=port, proxy_type="HTTP"))
                
                if proxies:
                    print(Fore.GREEN + f"[*] Création d'un rotateur pour {len(proxies)} proxys...")
                    rotator = create_proxy_rotator(proxies)
                    
                    # Test du rotateur
                    print(Fore.CYAN + "\n[INFO] Test du rotateur (5 premiers proxys) :")
                    for i in range(5):
                        proxy = rotator()
                        if proxy:
                            print(Fore.GREEN + f"  {i+1}. {proxy.ip}:{proxy.port}")
                    
                    print(Fore.GREEN + f"\n[+] Rotateur créé avec succès pour {len(proxies)} proxys")
                else:
                    print(Fore.RED + "Aucun proxy valide trouvé dans le fichier.")
            except FileNotFoundError:
                print(Fore.RED + f"Fichier '{filename}' non trouvé.")
            except Exception as e:
                print(Fore.RED + f"Erreur lors de la création du rotateur : {e}")
            prompt_to_continue()

        elif choix in proxy_scrape_options:
            proxy_type = proxy_scrape_options[choix]
            print(Fore.GREEN + f"[*] Scraping des proxys {proxy_type} en cours...")
            
            # Demander si l'utilisateur veut valider les proxys
            validate_choice = input(Fore.YELLOW + "Voulez-vous valider les proxys ? (o/n) : ").lower()
            validate = validate_choice in ['o', 'oui', 'y', 'yes']
            
            scraped_proxies = scrape_proxies(proxy_type, validate=validate)

            if scraped_proxies:
                # Demander le format de sauvegarde
                print(Fore.CYAN + "\nFormats disponibles :")
                print("1. Simple (IP:PORT)")
                print("2. Détaillé (avec métadonnées)")
                print("3. JSON")
                format_choice = input(Fore.YELLOW + "Choisissez le format (1-3) : ")
                
                format_map = {"1": "simple", "2": "detailed", "3": "json"}
                format_type = format_map.get(format_choice, "simple")
                
                filename = f"{proxy_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                if format_type == "json":
                    filename = filename.replace(".txt", ".json")
                
                save_proxies_to_file(filename, scraped_proxies, format_type)
            else:
                print(Fore.RED + f"Aucun proxy {proxy_type} trouvé.")
            prompt_to_continue()

        else:
            print(Fore.RED + f"Choix invalide. Veuillez entrer un chiffre entre {CHOICE_EXIT} et {CHOICE_CREATE_ROTATOR}.")
            prompt_to_continue()

if __name__ == "__main__":
    main()
