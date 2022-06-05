from dataclasses import replace
from pickle import FALSE, TRUE
from unittest import case
from pydub import AudioSegment
from pydub.silence import split_on_silence
import glob
import pandas as pd
import os

###############################################################################
# define
###############################################################################
# 環境変数定義（Do Not Modify)
EDITED_LIST_FILE = "edited_list.csv"
LIST_COL_NAME = "file"
INPUT_DIR_BASE = "./input/"
INPUT_DIR_E = INPUT_DIR_BASE + "Stock3000_1_E/"
INPUT_DIR_EJ = INPUT_DIR_BASE + "Stock3000_2_EJ/"
INPUT_DIR_EX = INPUT_DIR_BASE + "Stock3000_4_EX/"
OUTPUT_DIR_BASE = "./output/"
SOUND_MODE_EJ_BLNK_EX = 0
SOUND_MODE_EJ_EX_EX = 1
SOUND_MODE_EJ_BLNK_EX_EX = 2
SOUND_MODE_REG = [
    "Stock3000_EJ_BK_EX",
    "Stock3000_EJ_EX_EX", 
    "Stock3000_EJ_BK_EX_EX"
]

# 設定
SOUND_MODE = SOUND_MODE_EJ_BLNK_EX_EX
OUTPUT_CHUNK_NUM = 60
DEBUG_MODE = FALSE

# 環境変数定義(その2 Do Not Modify)
OUTPUT_TITLE = SOUND_MODE_REG[SOUND_MODE]
OUTPUT_DIR_PREFIX = OUTPUT_DIR_BASE + OUTPUT_TITLE + "/"

###############################################################################
# クラス
###############################################################################
class SoundProcMod:

    silent_200ms = AudioSegment.silent(duration=200)
    silent_1000ms = AudioSegment.silent(duration=1000)
    silent_1500ms = AudioSegment.silent(duration=1500)
    silent_10s = AudioSegment.silent(duration=10000)
    
    def __init__(self):
        self.output_dir = None

    # 音声処理
    def ProcessSound(self, file_ex, file_ej, filename_prefix, word_index):

        # 音声ファイルLoad
        sound_ex = AudioSegment.from_file(file_ex, format="mp3")
        sound_ej = AudioSegment.from_file(file_ej, format="mp3")

        # wavデータの分割（無音部分で区切る）
        chunks_ex = split_on_silence(sound_ex, min_silence_len=980, silence_thresh=-40, keep_silence=100)
        chunks_ej = split_on_silence(sound_ej, min_silence_len=980, silence_thresh=-40, keep_silence=100)

        # 生成したファイル数のチェック
        print(len(chunks_ex), len(chunks_ej))
        if(len(chunks_ex)*2 != len(chunks_ej)):
            print("Error. chunks_length is invalid")
            for i, chunk_ex in enumerate(chunks_ex):
                chunk_ex.export("./debug/chunk_ex_" + str(i) +".mp3", format="mp3")
            for i, chunk_ej in enumerate(chunks_ej):
                chunk_ej.export("./debug/chunk_ej_" + str(i) +".mp3", format="mp3")
            exit()

        # 正常に音声が生成できたら編集済みリストに追記する
        if DEBUG_MODE == TRUE:
            df_edited_list = pd.concat([df_edited_list, pd.DataFrame(data=[filename_ex], columns=["file"])])
            df_edited_list.to_csv(EDITED_LIST_FILE, index=False)

        # 例文ファイルをベースに1単語ずつ音声ファイルを生成
        saved_file_num = 0
        for i, chunk_ex in enumerate(chunks_ex):
            word_index += 1
            saved_file_num += 1

            # 指定した単語数単位にフォルダを分ける
            if word_index % OUTPUT_CHUNK_NUM == 1: # 1オリジンのため
                dir_index = int(word_index / OUTPUT_CHUNK_NUM)
                word_index_st = (dir_index * OUTPUT_CHUNK_NUM) + 1
                word_index_ed = ((dir_index + 1) * OUTPUT_CHUNK_NUM)
                self.output_dir = OUTPUT_DIR_PREFIX + OUTPUT_TITLE + "_" + str(word_index_st).zfill(4) + "_" + str(word_index_ed).zfill(4) + "/"
                os.makedirs(self.output_dir, exist_ok=True)

            # Progress表示
            print(i+1, "/", len(chunks_ex), ",", file_index+1,  "/", len(files_ex))

            # 音声ファイル生成
            chunk_duration = chunk_ex.duration_seconds * 1000
            silent_ex = AudioSegment.silent(duration=chunk_duration)
            if SOUND_MODE == SOUND_MODE_EJ_BLNK_EX:
                record = SoundProcMod.silent_200ms + chunks_ej[i * 2] + SoundProcMod.silent_1000ms + chunks_ej[i * 2 + 1] + SoundProcMod.silent_1000ms + silent_ex + chunk_ex + silent_ex
            elif SOUND_MODE == SOUND_MODE_EJ_EX_EX:
                record = SoundProcMod.silent_200ms + chunks_ej[i * 2] + SoundProcMod.silent_1000ms + chunks_ej[i * 2 + 1] + SoundProcMod.silent_1000ms + chunk_ex + SoundProcMod.silent_1500ms + chunk_ex + silent_ex
            elif SOUND_MODE == SOUND_MODE_EJ_BLNK_EX_EX:
                record = SoundProcMod.silent_200ms + chunks_ej[i * 2] + SoundProcMod.silent_1000ms + chunks_ej[i * 2 + 1] + SoundProcMod.silent_10s + chunk_ex + SoundProcMod.silent_1500ms + chunk_ex + silent_ex

            # 出力ディレクトリが有効なら出力
            if self.output_dir != None:
                save_filename = self.output_dir + SOUND_MODE_REG[SOUND_MODE] + "_" + str(word_index).zfill(4) +".mp3"
                record.export(save_filename, format="mp3")
            else:
                print("Error: output_dir is invalid")
                exit()

        return saved_file_num

###############################################################################
# 関数
###############################################################################

###############################################################################
# メイン
###############################################################################
# 音声ファイルLoad
files_ej = sorted(glob.glob(INPUT_DIR_EJ + "*"))
files_ex = sorted(glob.glob(INPUT_DIR_EX + "*"))

# デバッグモード対応
# 途中でエラー停止した際、毎回先頭から再開しないで済むよう完了したファイルを記録しておき、
# 途中から再開できるようにする
if DEBUG_MODE == TRUE:
    edited_list = pd.read_csv(EDITED_LIST_FILE)
    df_edited_list = pd.DataFrame(data=edited_list, columns=["file"])

# 処理単語数
word_index = 0

# 例文、音声/日本語ファイルは10単語ずつになっているため、
# 1単語ずつに分解し、任意の組み合わせで音声ファイルを生成する（日本語＋英語＋例文x2など）
# 分割したデータ毎にファイルに出力
proc_mod = SoundProcMod()
for file_index, file_ex in enumerate(files_ex):
    
    # ファイル名取得
    path_ex_split = file_ex.split("/")
    filename_ex = path_ex_split[3]
    page_no = int(filename_ex.split("_")[1].replace("p", ""))
    file_ej = INPUT_DIR_EJ + "Stock3000_p" + format((page_no-1), "03") + "_EJ.mp3"
    print(file_ex)
    print(file_ej)
    filename_prefix = file_ex.split("/")[2].split(".")[0]

    # 音声処理
    if DEBUG_MODE == TRUE:
        # 対象の例文ファイルが編集済みリストにあるかサーチ
        # 無ければ追加
        # 既にあるなら以降の処理をスキップ
        # 対象のファイル名検索
        file_match_num = (df_edited_list[LIST_COL_NAME] == filename_ex).sum()
        if (file_match_num > 0):
            print("Already Edited. :", filename_ex)
        else:
            word_index += proc_mod.ProcessSound(file_ex, file_ej, filename_prefix, word_index)

    else:
        word_index += proc_mod.ProcessSound(file_ex, file_ej, filename_prefix, word_index)