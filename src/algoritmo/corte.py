def cortar_chapas(largura_chapa_cm: float, altura_chapa_cm: float, pecas: list) -> tuple:
    """
    Algoritmo de otimização de corte de chapas.
    
    Args:
        largura_chapa_cm: Largura da chapa em centímetros
        altura_chapa_cm: Altura da chapa em centímetros
        pecas: Lista de peças a serem cortadas, cada peça é um dicionário com:
            - id: identificador da peça
            - larg: largura em centímetros
            - alt: altura em centímetros
            - original_idx: índice original da peça
            
    Returns:
        Tuple contendo:
        - Lista de chapas com suas peças alocadas
        - Lista de peças não alocadas
    """
    # Ordena as peças por área (maior para menor)
    pecas_ordenadas = sorted(pecas, key=lambda p: p['larg'] * p['alt'], reverse=True)
    
    # Lista para armazenar as chapas cortadas
    chapas_cortadas = []
    pecas_nao_alocadas = []
    
    # Função para verificar se uma peça cabe em um espaço
    def peca_cabe_em_espaco(peca, espaco):
        # Verifica se a peça tem as propriedades originais ou alocadas
        largura = peca.get('larg', peca.get('largura', 0))
        altura = peca.get('alt', peca.get('altura', 0))
        return (largura <= espaco['largura'] and 
                altura <= espaco['altura'])
    
    # Função para criar novos espaços após colocar uma peça
    def criar_novos_espacos(espaco, peca):
        novos_espacos = []
        
        # Obtém as dimensões da peça
        largura = peca.get('larg', peca.get('largura', 0))
        altura = peca.get('alt', peca.get('altura', 0))
        
        # Espaço à direita da peça
        if espaco['largura'] - largura > 0:
            novos_espacos.append({
                'x': espaco['x'] + largura,
                'y': espaco['y'],
                'largura': espaco['largura'] - largura,
                'altura': altura
            })
            
        # Espaço abaixo da peça
        if espaco['altura'] - altura > 0:
            novos_espacos.append({
                'x': espaco['x'],
                'y': espaco['y'] + altura,
                'largura': espaco['largura'],
                'altura': espaco['altura'] - altura
            })
            
        return novos_espacos
    
    # Função para encontrar o melhor espaço para uma peça
    def encontrar_melhor_espaco(peca, espacos):
        melhor_espaco = None
        melhor_pontuacao = float('inf')
        
        for espaco in espacos:
            if peca_cabe_em_espaco(peca, espaco):
                # Obtém as dimensões da peça
                largura = peca.get('larg', peca.get('largura', 0))
                altura = peca.get('alt', peca.get('altura', 0))
                # Pontuação baseada na área residual
                area_residual = (espaco['largura'] * espaco['altura']) - (largura * altura)
                if area_residual < melhor_pontuacao:
                    melhor_pontuacao = area_residual
                    melhor_espaco = espaco
                    
        return melhor_espaco
    
    # Função para tentar realocar peças entre chapas
    def tentar_realocar_pecas():
        for i, chapa in enumerate(chapas_cortadas):
            for j, outra_chapa in enumerate(chapas_cortadas[i+1:], i+1):
                for peca in chapa['pecas_alocadas']:
                    # Verifica se a peça cabe na outra chapa
                    espacos = [{
                        'x': 0,
                        'y': 0,
                        'largura': largura_chapa_cm,
                        'altura': altura_chapa_cm
                    }]
                    
                    # Remove os espaços ocupados pelas peças existentes
                    for p in outra_chapa['pecas_alocadas']:
                        novos_espacos = []
                        for espaco in espacos:
                            if (espaco['x'] < p['x'] + p['largura'] and
                                espaco['x'] + espaco['largura'] > p['x'] and
                                espaco['y'] < p['y'] + p['altura'] and
                                espaco['y'] + espaco['altura'] > p['y']):
                                
                                # Divide o espaço em partes não sobrepostas
                                if espaco['x'] < p['x']:
                                    novos_espacos.append({
                                        'x': espaco['x'],
                                        'y': espaco['y'],
                                        'largura': p['x'] - espaco['x'],
                                        'altura': espaco['altura']
                                    })
                                if espaco['x'] + espaco['largura'] > p['x'] + p['largura']:
                                    novos_espacos.append({
                                        'x': p['x'] + p['largura'],
                                        'y': espaco['y'],
                                        'largura': espaco['x'] + espaco['largura'] - (p['x'] + p['largura']),
                                        'altura': espaco['altura']
                                    })
                                if espaco['y'] < p['y']:
                                    novos_espacos.append({
                                        'x': espaco['x'],
                                        'y': espaco['y'],
                                        'largura': espaco['largura'],
                                        'altura': p['y'] - espaco['y']
                                    })
                                if espaco['y'] + espaco['altura'] > p['y'] + p['altura']:
                                    novos_espacos.append({
                                        'x': espaco['x'],
                                        'y': p['y'] + p['altura'],
                                        'largura': espaco['largura'],
                                        'altura': espaco['y'] + espaco['altura'] - (p['y'] + p['altura'])
                                    })
                            else:
                                novos_espacos.append(espaco)
                        espacos = novos_espacos
                    
                    # Tenta colocar a peça em algum espaço, considerando a rotação
                    melhor_espaco = None
                    melhor_pontuacao = float('inf')
                    melhor_rotacao = False
                    
                    # Tenta sem rotação
                    for espaco in espacos:
                        if peca_cabe_em_espaco(peca, espaco):
                            area_residual = (espaco['largura'] * espaco['altura']) - (peca['largura'] * peca['altura'])
                            if area_residual < melhor_pontuacao:
                                melhor_pontuacao = area_residual
                                melhor_espaco = espaco
                                melhor_rotacao = False
                    
                    # Tenta com rotação
                    peca_rotacionada = {
                        'largura': peca['altura'],
                        'altura': peca['largura']
                    }
                    for espaco in espacos:
                        if peca_cabe_em_espaco(peca_rotacionada, espaco):
                            area_residual = (espaco['largura'] * espaco['altura']) - (peca_rotacionada['largura'] * peca_rotacionada['altura'])
                            if area_residual < melhor_pontuacao:
                                melhor_pontuacao = area_residual
                                melhor_espaco = espaco
                                melhor_rotacao = True
                    
                    if melhor_espaco:
                        # Move a peça para a outra chapa
                        peca['x'] = melhor_espaco['x']
                        peca['y'] = melhor_espaco['y']
                        if melhor_rotacao:
                            peca['largura'], peca['altura'] = peca['altura'], peca['largura']
                            peca['rotacionada'] = not peca.get('rotacionada', False)
                        outra_chapa['pecas_alocadas'].append(peca)
                        chapa['pecas_alocadas'].remove(peca)
                        
                        # Se a chapa original ficou vazia, remove ela
                        if not chapa['pecas_alocadas']:
                            chapas_cortadas.remove(chapa)
                        return True
        return False
    
    # Aloca as peças nas chapas
    for peca in pecas_ordenadas:
        peca_alocada = False
        
        # Tenta alocar a peça em uma chapa existente
        for chapa in chapas_cortadas:
            espacos = [{
                'x': 0,
                'y': 0,
                'largura': largura_chapa_cm,
                'altura': altura_chapa_cm
            }]
            
            # Remove os espaços ocupados pelas peças existentes
            for p in chapa['pecas_alocadas']:
                novos_espacos = []
                for espaco in espacos:
                    if (espaco['x'] < p['x'] + p['largura'] and
                        espaco['x'] + espaco['largura'] > p['x'] and
                        espaco['y'] < p['y'] + p['altura'] and
                        espaco['y'] + espaco['altura'] > p['y']):
                        
                        # Divide o espaço em partes não sobrepostas
                        if espaco['x'] < p['x']:
                            novos_espacos.append({
                                'x': espaco['x'],
                                'y': espaco['y'],
                                'largura': p['x'] - espaco['x'],
                                'altura': espaco['altura']
                            })
                        if espaco['x'] + espaco['largura'] > p['x'] + p['largura']:
                            novos_espacos.append({
                                'x': p['x'] + p['largura'],
                                'y': espaco['y'],
                                'largura': espaco['x'] + espaco['largura'] - (p['x'] + p['largura']),
                                'altura': espaco['altura']
                            })
                        if espaco['y'] < p['y']:
                            novos_espacos.append({
                                'x': espaco['x'],
                                'y': espaco['y'],
                                'largura': espaco['largura'],
                                'altura': p['y'] - espaco['y']
                            })
                        if espaco['y'] + espaco['altura'] > p['y'] + p['altura']:
                            novos_espacos.append({
                                'x': espaco['x'],
                                'y': p['y'] + p['altura'],
                                'largura': espaco['largura'],
                                'altura': espaco['y'] + espaco['altura'] - (p['y'] + p['altura'])
                            })
                    else:
                        novos_espacos.append(espaco)
                espacos = novos_espacos
            
            # Tenta colocar a peça em algum espaço
            melhor_espaco = encontrar_melhor_espaco(peca, espacos)
            if melhor_espaco:
                # Cria uma cópia da peça com todas as propriedades necessárias
                peca_alocada = {
                    'id': peca['id'],
                    'x': melhor_espaco['x'],
                    'y': melhor_espaco['y'],
                    'largura': peca['larg'],
                    'altura': peca['alt'],
                    'original_idx': peca['original_idx']
                }
                chapa['pecas_alocadas'].append(peca_alocada)
                peca_alocada = True
                break
        
        # Se não conseguiu alocar, cria uma nova chapa
        if not peca_alocada:
            if peca['larg'] <= largura_chapa_cm and peca['alt'] <= altura_chapa_cm:
                nova_chapa = {
                    'pecas_alocadas': [{
                        'id': peca['id'],
                        'x': 0,
                        'y': 0,
                        'largura': peca['larg'],
                        'altura': peca['alt'],
                        'original_idx': peca['original_idx']
                    }]
                }
                chapas_cortadas.append(nova_chapa)
                peca_alocada = True
            else:
                pecas_nao_alocadas.append(peca)
    
    # Tenta realocar peças entre chapas para otimizar o espaço
    while tentar_realocar_pecas():
        pass
    
    return chapas_cortadas, pecas_nao_alocadas 