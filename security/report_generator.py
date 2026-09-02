#!/usr/bin/env python3
"""
Gênesis Córtex - Report Generator
Gera relatórios de segurança em Markdown
"""

import logging
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    """Gerador de relatórios de segurança"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_scan_report(self, scan_data: Dict[str, Any], output_path: str = None) -> str:
        """Gera relatório de varredura de código"""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"scan_report_{timestamp}.md"
        else:
            output_path = Path(output_path)
            
        report_content = self._generate_scan_markdown(scan_data)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"Relatório gerado: {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return ""
            
    def generate_dependency_report(self, dep_data: Dict[str, Any], output_path: str = None) -> str:
        """Gera relatório de dependências"""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"dependency_report_{timestamp}.md"
        else:
            output_path = Path(output_path)
            
        report_content = self._generate_dependency_markdown(dep_data)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"Relatório gerado: {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return ""
            
    def generate_binary_report(self, binary_data: Dict[str, Any], output_path: str = None) -> str:
        """Gera relatório de análise de binário"""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"binary_report_{timestamp}.md"
        else:
            output_path = Path(output_path)
            
        report_content = self._generate_binary_markdown(binary_data)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"Relatório gerado: {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return ""
            
    def _generate_scan_markdown(self, scan_data: Dict[str, Any]) -> str:
        """Gera markdown para relatório de scan"""
        
        if "error" in scan_data:
            return f"# Relatório de Erro\n\n{scan_data['error']}"
            
        if "directory" in scan_data:
            # Relatório de diretório
            markdown = f"""# Relatório de Varredura de Segurança

**Diretório:** `{scan_data['directory']}`  
**Data:** {scan_data['scan_time']}  
**Arquivos Escaneados:** {scan_data['files_scanned']}

## Resumo

| Severidade | Quantidade |
|------------|------------|
| Críticas | {scan_data['critical']} |
| Altas | {scan_data['high']} |
| Médias | {scan_data['medium']} |
| Baixas | {scan_data['low']} |
| **Total** | **{scan_data['total_vulnerabilities']}** |

## Detalhes por Arquivo

"""
            for result in scan_data['results']:
                markdown += f"""### {result['file']}

**Linguagem:** {result['language']}  
**Hash:** `{result['hash']}`  
**Vulnerabilidades:** {result['total']}

"""
                if result['vulnerabilities']:
                    for vuln in result['vulnerabilities']:
                        markdown += f"""- **{vuln['type']}** ({vuln['severity']})
  - Linha: {vuln['line']}
  - Descrição: {vuln['description']}
  - Regra: {vuln['rule']}

"""
                else:
                    markdown += "*Nenhuma vulnerabilidade encontrada*\n\n"
                    
        else:
            # Relatório de arquivo único
            markdown = f"""# Relatório de Varredura de Segurança

**Arquivo:** `{scan_data['file']}`  
**Linguagem:** {scan_data['language']}  
**Hash:** `{scan_data['hash']}`

## Resumo

| Severidade | Quantidade |
|------------|------------|
| Críticas | {scan_data['critical']} |
| Altas | {scan_data['high']} |
| Médias | {scan_data['medium']} |
| Baixas | {scan_data['low']} |
| **Total** | **{scan_data['total']}** |

## Detalhes

"""
            if scan_data['vulnerabilities']:
                for vuln in scan_data['vulnerabilities']:
                    markdown += f"""### {vuln['type']} ({vuln['severity']})

- **Linha:** {vuln['line']}
- **Descrição:** {vuln['description']}
- **Regra:** {vuln['rule']}

"""
            else:
                markdown += "*Nenhuma vulnerabilidade encontrada*\n"
                
        markdown += f"""
---
*Relatório gerado por Gênesis Córtex em {datetime.now().isoformat()}*
"""
        return markdown
        
    def _generate_dependency_markdown(self, dep_data: Dict[str, Any]) -> str:
        """Gera markdown para relatório de dependências"""
        
        if "error" in dep_data:
            return f"# Relatório de Erro\n\n{dep_data['error']}"
            
        if "directory" in dep_data:
            # Relatório de diretório
            markdown = f"""# Relatório de Vulnerabilidades em Dependências

**Diretório:** `{dep_data['directory']}`  
**Data:** {dep_data['check_time']}  
**Arquivos Verificados:** {dep_data['files_checked']}

## Resumo

**Total de Dependências Verificadas:** {sum(r['dependencies_checked'] for r in dep_data['results'])}  
**Total de Vulnerabilidades:** {dep_data['total_vulnerabilities']}

## Detalhes por Arquivo

"""
            for result in dep_data['results']:
                markdown += f"""### {result['file']}

**Ecossistema:** {result['ecosystem']}  
**Dependências:** {result['dependencies_checked']}  
**Vulnerabilidades:** {result['total_vulnerabilities']}

"""
                for dep in result['results']:
                    if dep['count'] > 0:
                        markdown += f"""#### {dep['package']} ({dep['version']})

**Vulnerabilidades encontradas:** {dep['count']}

"""
                        for vuln in dep['vulnerabilities']:
                            markdown += f"""- **{vuln['id']}**
  - Severidade: {vuln.get('severity', 'UNKNOWN')}
  - Resumo: {vuln.get('summary', 'N/A')}
  - Publicado: {vuln.get('published', 'N/A')}

"""
                    else:
                        markdown += f"- {dep['package']} ({dep['version'}): ✅ Sem vulnerabilidades\n\n"
                        
        else:
            # Relatório de arquivo único
            markdown = f"""# Relatório de Vulnerabilidades em Dependências

**Arquivo:** `{dep_data['file']}`  
**Ecossistema:** {dep_data['ecosystem']}  
**Data:** {dep_data['check_time']}

## Resumo

**Dependências Verificadas:** {dep_data['dependencies_checked']}  
**Total de Vulnerabilidades:** {dep_data['total_vulnerabilities']}

## Detalhes

"""
            for dep in dep_data['results']:
                if dep['count'] > 0:
                    markdown += f"""### {dep['package']} ({dep['version']})

**Vulnerabilidades encontradas:** {dep['count']}

"""
                    for vuln in dep['vulnerabilities']:
                        markdown += f"""- **{vuln['id']}**
  - Severidade: {vuln.get('severity', 'UNKNOWN')}
  - Resumo: {vuln.get('summary', 'N/A')}
  - Publicado: {vuln.get('published', 'N/A')}

"""
                else:
                    markdown += f"- {dep['package']} ({dep['version']}): ✅ Sem vulnerabilidades\n\n"
                    
        markdown += f"""
---
*Relatório gerado por Gênesis Córtex em {datetime.now().isoformat()}*
"""
        return markdown
        
    def _generate_binary_markdown(self, binary_data: Dict[str, Any]) -> str:
        """Gera markdown para relatório de binário"""
        
        if "error" in binary_data:
            return f"# Relatório de Erro\n\n{binary_data['error']}"
            
        markdown = f"""# Relatório de Análise de Binário

**Tipo:** {binary_data['type']}  
**Arquitetura:** {binary_data.get('architecture', 'UNKNOWN')}  
**Ponto de Entrada:** {binary_data.get('entry_point', 'N/A')}

## Hashes

| Algoritmo | Hash |
|-----------|------|
| SHA-256 | `{binary_data['hashes']['sha256']}` |
| SHA-1 | `{binary_data['hashes']['sha1']}` |
| MD5 | `{binary_data['hashes']['md5']}` |

## Informações Específicas

"""
        if binary_data['type'] == "ELF":
            markdown += f"""- **Tipo de Arquivo:** {binary_data.get('file_type', 'UNKNOWN')}
- **Offset Program Header:** {binary_data.get('program_header_offset', 'N/A')}
- **Offset Section Header:** {binary_data.get('section_header_offset', 'N/A')}
- **Flags:** {binary_data.get('flags', 'N/A')}

"""
        elif binary_data['type'] == "PE":
            markdown += f"""- **Base de Imagem:** {binary_data.get('image_base', 'N/A')}
- **Número de Seções:** {binary_data.get('num_sections', 'N/A')}

"""
        elif binary_data['type'] == "Mach-O":
            markdown += f"""- **Tipo de Arquivo:** {binary_data.get('file_type', 'UNKNOWN')}

"""
        
        if binary_data.get('security_flags'):
            markdown += "## Flags de Segurança\n\n"
            for flag in binary_data['security_flags']:
                markdown += f"- {flag}\n"
            markdown += "\n"
            
        if binary_data.get('suspicious_sections'):
            markdown += "## Seções Suspeitas\n\n"
            for section in binary_data['suspicious_sections']:
                markdown += f"- {section}\n"
            markdown += "\n"
            
        markdown += f"""
---
*Relatório gerado por Gênesis Córtex em {datetime.now().isoformat()}*
"""
        return markdown