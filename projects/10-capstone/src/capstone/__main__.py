import os
import sys

from .cli import main

code = main()
sys.stdout.flush()
sys.stderr.flush()
# Workaround documentado: com deltalake 1.6 + pyarrow 25, threads nativas vivas no encerramento do interpretador
# às vezes derrubam o processo (`terminate called without an active exception`, exit 134) DEPOIS de o trabalho
# terminar com sucesso. Como tudo já foi gravado e descarregado, saímos direto com o código correto.
os._exit(code)
