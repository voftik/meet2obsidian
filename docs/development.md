#  07@01>B:0 meet2obsidian

## 17>@

Meet2Obsidian - MB> 8=AB@C<5=B 4;O ?@5>1@07>20=8O 70?8A59 2AB@5G 2 AB@C:BC@8@>20==K5 70<5B:8 2 Obsidian. = 8A?>;L7C5B AI 4;O B@0=A:@810F88 8 0=0;870 0C48>/2845> D09;>2 8 A>740=8O 70<5B>: A CGQB>< :>=B5:AB0.

## !B@C:BC@0 ?@>5:B0

@>5:B >@30=87>20= 2 A;54CNI85 >A=>2=K5 <>4C;8:

- **meet2obsidian.api** - =B53@0F8O A 2=5H=8<8 API (Claude, Rev.ai)
- **meet2obsidian.audio** - 1@01>B:0 0C48> 8 2845> D09;>2
- **meet2obsidian.note** - 5=5@0F8O 8 D>@<0B8@>20=85 70<5B>:
- **meet2obsidian.utils** - A?><>30B5;L=K5 CB8;8BK (;>38@>20=85, 157>?0A=>ABL)
- **meet2obsidian.core** - A=>2=>9 DC=:F8>=0; 8 >1@01>B:0 ?09?;09=0
- **meet2obsidian.cli** - =B5@D59A :><0=4=>9 AB@>:8
- **meet2obsidian.config** - #?@02;5=85 :>=D83C@0F859
- **meet2obsidian.monitor** - >=8B>@8=3 48@5:B>@89 8 >1@01>B:0 =>2KE D09;>2

## A=>2=K5 :><?>=5=BK

;O ?>;CG5=8O ?>4@>1=>9 8=D>@<0F88 > :064>< :><?>=5=B5, A<>B@8B5 4>:C<5=B0F8N 2 @0745;5 `dev/components/`:

- [API Key Management](dev/components/API%20Key%20Management.md) - #?@02;5=85 :;NG0<8 API
- [Logging](dev/components/Logging.md) - !8AB5<0 ;>38@>20=8O

##  01>G89 ?@>F5AA @07@01>B:8

### 0AB@>9:0 >:@C65=8O

1. ;>=8@>20BL @5?>78B>@89:
   ```bash
   git clone https://github.com/yourusername/meet2obsidian.git
   cd meet2obsidian
   ```

2. !>740BL 8 0:B828@>20BL 28@BC0;L=>5 >:@C65=85:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate  # Windows
   ```

3. #AB0=>28BL 7028A8<>AB8:
   ```bash
   pip install -r requirements.txt
   ```

### 0?CA: B5AB>2

```bash
pytest tests/
```

;O 70?CA:0 :>=:@5B=>3> =01>@0 B5AB>2:
```bash
pytest tests/unit/test_logging.py
```

### !B8;L :>40

@>5:B A;54C5B AB0=40@B0< PEP 8 4;O Python. A?>;L7C9B5 `black` 8 `flake8` 4;O D>@<0B8@>20=8O 8 ?@>25@:8 :>40:

```bash
black meet2obsidian/ tests/
flake8 meet2obsidian/ tests/
```

## >:C<5=B0F8O

>:C<5=B0F8O ?@>5:B0 @0745;5=0 =0 A;54CNI85 @0745;K:

- **/docs/user/** - >;L7>20B5;LA:0O 4>:C<5=B0F8O
- **/docs/dev/** - >:C<5=B0F8O 4;O @07@01>BG8:>2
- **/docs/api/** - >:C<5=B0F8O API

;O A>740=8O =>2>9 4>:C<5=B0F88 :><?>=5=B0, 8A?>;L7C9B5 H01;>= 2 `/docs/assets/templates/component-template.md`.

##  01>G89 ?@>F5AA A Git

1. !>7409B5 25B:C 4;O =>2>9 DC=:F88 8;8 8A?@02;5=8O:
   ```bash
   git checkout -b feature/my-feature
   ```

2. =5A8B5 87<5=5=8O 8 70D8:A8@C9B5 8E:
   ```bash
   git add .
   git commit -m ">102;5=0 =>20O DC=:F8O X"
   ```

3. B?@02LB5 87<5=5=8O 2 @5?>78B>@89:
   ```bash
   git push origin feature/my-feature
   ```

4. !>7409B5 Pull Request 4;O >1J548=5=8O 87<5=5=89 2 >A=>2=CN 25B:C.

## >@>6=0O :0@B0

=D>@<0F8N > ?;0=8@C5<KE DC=:F8OE 8 7040G0E <>6=> =09B8 2 [4>@>6=>9 :0@B5](internal_docs/>@>6=0O%20:0@B0.md).