# Overview
blenderオブジェクトを選択して任意のorientationを定義するアドオン

# How to use
このリポジトリをzipダウンロードすれば使用可能 
標準のGloval、Localのorientationと4種類方法でと任意のorientationを定義する  
- object
    - 選択したオブジェクトの座標系からorientationを定義する
- vertex
    - 頂点を選択しその位置関係からorientationを定義する
    - 頂点1を原点とし、頂点1から2の方向がz軸方向となる
    - 定義したz軸から頂点3の方向がx軸方向となる(頂点3がない場合自動でx,y軸は定義する)
    - 複数選択した頂点をセットした場合は中点が座標となる
- edge
    - 辺を選択しその位置関係からorientationを定義する
    - 選択した辺がz軸方向となる
    - 定義したz軸から頂点3の方向がx軸方向となる(頂点3がない場合自動でx,y軸は定義する)
- bone
    - 選択したboneの座標系からorientationを定義する
詳細は
[note](https://note.com/preview/na7c62aa49036?prev_access_key=f527c29eba77038077dcc350fdd95c4b)
参照

# Revision
v0.0.1: 2025/04/21  
製作開始

