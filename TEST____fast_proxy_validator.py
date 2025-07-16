#!/usr/bin/env python3
"""
Script de validation rapide pour gros volumes de proxys
Optimisé pour traiter des dizaines de milliers de proxys rapidement
"""

import requests
import os
import time
import concurrent.futures
import json
import re
import signal
import sys
from datetime import datetime
from colorama import Fore, init
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

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
class FastProxy:
    """Proxy simplifié pour validation rapide."""
    ip: str
    port: str
    proxy_type: str = "HTTP"

def validate_proxy_format(proxy_str: str) -> Optional[Tuple[str, str]]:
    """Validation rapide du format proxy."""
    match = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})', proxy_str.strip())
    if match:
        ip, port = match.group(1), match.group(2)
        try:
            port_num = int(port)
            if 1 <= port_num <= 65535:
                return ip, port
        except:
            pass
    return None

def test_proxy_fast(proxy: FastProxy, timeout: int = 2) -> bool:
    """Test ultra-rapide d'un proxy."""
    global interrupt_flag
    if interrupt_flag:
        return False
        
    try:
        proxy_dict = {
            'http': f'http://{proxy.ip}:{proxy.port}',
            'https': f'http://{proxy.ip}:{proxy.port}'
        }
        
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxy_dict,
            timeout=timeout
        )
        return response.status_code == 200
    except:
        return False

def load_proxies_from_file(filename: str) -> List[FastProxy]:
    """Charge les proxys depuis un fichier."""
    proxies = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                proxy_info = validate_proxy_format(line)
                if proxy_info:
                    ip, port = proxy_info
                    proxies.append(FastProxy(ip=ip, port=port))
                else:
                    print(Fore.YELLOW + f"[WARN] Ligne {line_num} ignorée: {line}")
        
        return proxies
    except Exception as e:
        print(Fore.RED + f"Erreur lors du chargement: {e}")
        return []

def validate_proxies_ultra_fast(proxies: List[FastProxy], batch_size: int = 500, max_workers: int = 50) -> List[FastProxy]:
    """Validation ultra-rapide par batch."""
    global interrupt_flag
    interrupt_flag = False
    working_proxies = []
    total_proxies = len(proxies)
    
    print(Fore.CYAN + f"[INFO] Validation ultra-rapide de {total_proxies:,} proxys")
    print(Fore.CYAN + f"[INFO] Batch size: {batch_size}, Workers: {max_workers}")
    print(Fore.YELLOW + "[INFO] Appuyez sur Ctrl+C pour interrompre la validation")
    
    start_time = time.time()
    
    for i in range(0, total_proxies, batch_size):
        if interrupt_flag:
            print(Fore.YELLOW + "\n[INFO] Validation interrompue par l'utilisateur")
            break
            
        batch = proxies[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_proxies + batch_size - 1) // batch_size
        
        print(Fore.YELLOW + f"\n[INFO] Batch {batch_num}/{total_batches} ({len(batch):,} proxys)...")
        
        batch_start = time.time()
        
        # Validation du batch en parallèle
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {executor.submit(test_proxy_fast, proxy): proxy for proxy in batch}
            
            completed = 0
            batch_working = 0
            
            for future in concurrent.futures.as_completed(future_to_proxy):
                if interrupt_flag:
                    break
                    
                proxy = future_to_proxy[future]
                completed += 1
                
                try:
                    if future.result():
                        working_proxies.append(proxy)
                        batch_working += 1
                except Exception:
                    continue
                
                # Affichage de progression tous les 50 proxys
                if completed % 50 == 0 or completed == len(batch):
                    progress = (completed / len(batch)) * 100
                    elapsed = time.time() - batch_start
                    rate = completed / elapsed if elapsed > 0 else 0
                    print(Fore.GREEN + f"  {progress:.1f}% - {batch_working} fonctionnels - {rate:.0f} proxys/s")
        
        if interrupt_flag:
            break
            
        batch_time = time.time() - batch_start
        print(Fore.CYAN + f"  Batch terminé en {batch_time:.1f}s - {batch_working} fonctionnels")
        
        # Pause très courte entre les batchs
        time.sleep(0.1)
    
    total_time = time.time() - start_time
    print(Fore.GREEN + f"\n[INFO] Validation terminée en {total_time:.1f}s")
    print(Fore.GREEN + f"[INFO] {len(working_proxies):,} proxys fonctionnels sur {total_proxies:,}")
    if total_proxies > 0:
        print(Fore.GREEN + f"[INFO] Taux de succès: {(len(working_proxies)/total_proxies)*100:.1f}%")
    
    return working_proxies

def save_proxies_fast(filename: str, proxies: List[FastProxy]) -> None:
    """Sauvegarde rapide des proxys."""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            for proxy in proxies:
                file.write(f"{proxy.ip}:{proxy.port}\n")
        
        print(Fore.GREEN + f"[+] {len(proxies):,} proxys sauvegardés dans '{filename}'")
    except Exception as e:
        print(Fore.RED + f"Erreur lors de la sauvegarde: {e}")

def main():
    """Interface principale pour validation rapide."""
    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + "🚀 VALIDATEUR ULTRA-RAPIDE DE PROXYS")
    print(Fore.CYAN + "=" * 60)
    
    while True:
        print(Fore.YELLOW + "\nOptions disponibles:")
        print("1. Valider un fichier de proxys")
        print("2. Valider avec paramètres personnalisés")
        print("3. Quitter")
        
        choice = input(Fore.CYAN + "\nChoisissez une option (1-3): ").strip()
        
        if choice == "1":
            filename = input(Fore.YELLOW + "Entrez le nom du fichier de proxys: ").strip()
            
            if not os.path.exists(filename):
                print(Fore.RED + f"Fichier '{filename}' non trouvé!")
                continue
            
            print(Fore.GREEN + f"[*] Chargement du fichier '{filename}'...")
            proxies = load_proxies_from_file(filename)
            
            if not proxies:
                print(Fore.RED + "Aucun proxy valide trouvé dans le fichier!")
                continue
            
            print(Fore.GREEN + f"[*] {len(proxies):,} proxys chargés")
            
            # Validation avec paramètres par défaut
            working_proxies = validate_proxies_ultra_fast(proxies)
            
            if working_proxies:
                output_filename = f"validated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                save_proxies_fast(output_filename, working_proxies)
            else:
                print(Fore.RED + "Aucun proxy fonctionnel trouvé!")
        
        elif choice == "2":
            filename = input(Fore.YELLOW + "Entrez le nom du fichier de proxys: ").strip()
            
            if not os.path.exists(filename):
                print(Fore.RED + f"Fichier '{filename}' non trouvé!")
                continue
            
            # Paramètres personnalisés
            try:
                batch_size = int(input(Fore.YELLOW + "Taille du batch (défaut: 500): ") or "500")
                max_workers = int(input(Fore.YELLOW + "Nombre de workers (défaut: 50): ") or "50")
                timeout = int(input(Fore.YELLOW + "Timeout en secondes (défaut: 2): ") or "2")
            except ValueError:
                print(Fore.RED + "Paramètres invalides, utilisation des valeurs par défaut")
                batch_size, max_workers, timeout = 500, 50, 2
            
            print(Fore.GREEN + f"[*] Chargement du fichier '{filename}'...")
            proxies = load_proxies_from_file(filename)
            
            if not proxies:
                print(Fore.RED + "Aucun proxy valide trouvé dans le fichier!")
                continue
            
            print(Fore.GREEN + f"[*] {len(proxies):,} proxys chargés")
            print(Fore.CYAN + f"[INFO] Paramètres: batch_size={batch_size}, workers={max_workers}, timeout={timeout}s")
            
            # Validation avec paramètres personnalisés
            working_proxies = validate_proxies_ultra_fast(proxies, batch_size, max_workers)
            
            if working_proxies:
                output_filename = f"validated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                save_proxies_fast(output_filename, working_proxies)
            else:
                print(Fore.RED + "Aucun proxy fonctionnel trouvé!")
        
        elif choice == "3":
            print(Fore.RED + "Au revoir!")
            break
        
        else:
            print(Fore.RED + "Option invalide!")

if __name__ == "__main__":
    main() 