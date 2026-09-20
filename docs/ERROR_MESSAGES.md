# Error messages in every language

If you found this repository by searching for an error message, this page lists
the exact wordings. They are not translations made here — they are extracted
from macOS itself, from

```
/System/Library/PrivateFrameworks/AMPDevices.framework/Versions/A/Resources/Localizable.loctable
```

so they match character for character what Finder and iTunes display.

`^FILENAME` is replaced by your device name, `^ERRORNUMBER` and `^0` by an error
code.

**Which one you see depends on where the restore fails.** For this bug the first
message below is the closest match, but the generic variants appear too.

See the [README](../README.md) for what causes this and how to fix it.


## Some files could not be restored

The message that matches this bug most closely. iOS reports that individual
files could not be written -- which is exactly what the failing `rename` is.

**English** (`en`)

> Could not restore the iPhone “^FILENAME” because some files could not be restored from the backup.

**German** (`de`)

> Das iPhone „^FILENAME“ konnte nicht wiederhergestellt werden, da einige Dateien nicht aus dem Backup wiederhergestellt werden konnten.

**French** (`fr`)

> Impossible de restaurer l’iPhone « ^FILENAME » car certains fichiers n’ont pas pu être restaurés à partir de la sauvegarde.

**Spanish** (`es`)

> No se ha podido restaurar el iPhone “^FILENAME” porque algunos archivos no se han podido restaurar a partir de la copia de seguridad.

**Italian** (`it`)

> Impossibile ripristinare l’iPhone “^FILENAME” perché non è stato possibile ripristinare alcuni file dal backup.

**Dutch** (`nl`)

> De iPhone '^FILENAME' kon niet worden hersteld, omdat sommige bestanden niet konden worden teruggezet vanuit de back‑up.

**Portuguese (Brazil)** (`pt`)

> Não foi possível restaurar o iPhone “^FILENAME” porque alguns arquivos não puderam ser restaurados do backup.

**Portuguese (Portugal)** (`pt_PT`)

> Não foi possível restaurar o iPhone “^FILENAME”, porque não foi possível restaurar alguns ficheiros a partir da cópia de segurança.

**Polish** (`pl`)

> Nie można odtworzyć iPhone’a „^FILENAME”, ponieważ nie można przywrócić niektórych plików z backupu.

**Turkish** (`tr`)

> Bazı dosyalar yedekten geri yüklenemediği için “^FILENAME” adlı iPhone geri yüklenemedi.

**Russian** (`ru`)

> Не удалось восстановить iPhone «^FILENAME», так как некоторые файлы не удалось восстановить из резервной копии.

**Ukrainian** (`uk`)

> Не вдалося відновити iPhone «^FILENAME», оскільки з резервної копії не вдалося відновити деякі файли.

**Swedish** (`sv`)

> Kunde inte återställa iPhone-enheten ”^FILENAME” eftersom en del filer inte kunde återställas från säkerhetskopian.

**Danish** (`da`)

> Kunne ikke gendanne iPhone “^FILENAME”, fordi nogle arkiver ikke kunne gendannes fra sikkerhedskopien.

**Finnish** (`fi`)

> iPhonea ”^FILENAME” ei voida palauttaa, koska kaikkia varmuuskopiotiedostoja ei voitu palauttaa.

**Czech** (`cs`)

> iPhone „^FILENAME“ nelze obnovit, protože nelze obnovit některé soubory ze zálohy.

**Slovak** (`sk`)

> Nepodarilo sa obnoviť iPhone „^FILENAME“, pretože niektoré súbory sa nepodarilo obnoviť zo zálohy.

**Hungarian** (`hu`)

> Nem sikerült visszaállítani a(z) „^FILENAME” iPhone-t, mert néhány fájl nem állítható vissza a biztonsági másolatból.

**Romanian** (`ro`)

> iPhone‑ul „^FILENAME” nu a putut fi restaurat, deoarece unele fișiere nu au putut fi restaurate din backup.

**Croatian** (`hr`)

> Nije moguće obnoviti iPhone “^FILENAME” jer se neke datoteke ne mogu obnoviti iz sigurnosne kopije.

**Greek** (`el`)

> Δεν ήταν δυνατή η επαναφορά του iPhone «^FILENAME», διότι μερικά αρχεία ήταν δυνατό να επαναφερθούν από το εφεδρικό αντίγραφο.

**Japanese** (`ja`)

> 一部のファイルをバックアップから復元できなかったため、iPhone “^FILENAME”を復元できませんでした。

**Korean** (`ko`)

> 백업에서 일부 파일을 복원할 수 없기 때문에 ‘^FILENAME’ iPhone을 복원할 수 없습니다.

**Chinese (Simplified)** (`zh_CN`)

> 未能恢复iPhone“^FILENAME”，因为部分文件未能从备份中恢复。

**Chinese (Traditional)** (`zh_TW`)

> 無法回復iPhone「^FILENAME」，因為無法從備份回復部分檔案。

**Arabic** (`ar`)

> تعذرت استعادة الـ iPhone ‏"^FILENAME" بسبب تعذر استعادة بعض الملفات من النسخة الاحتياطية.

**Hebrew** (`he`)

> לא היתה אפשרות לשחזר את ה-iPhone ‏״^FILENAME״ מאחר שלא ניתן היה לשחזר מספר קבצים מהגיבוי.

**Thai** (`th`)

> ไม่สามารถกู้คืน iPhone “^FILENAME” เพราะบางไฟล์ไม่สามารถกู้คืนจากข้อมูลสำรองได้

**Vietnamese** (`vi`)

> Không thể khôi phục iPhone “^FILENAME” vì không thể khôi phục một số tệp từ bản sao lưu.

**Indonesian** (`id`)

> Tidak dapat memulihkan iPhone “^FILENAME” karena beberapa file tidak dapat dipulihkan dari cadangan.

**Malay** (`ms`)

> Tidak dapat memulihkan iPhone “^FILENAME” kerana sesetengah fail tidak dapat dipulihkan daripada sandaran.

**Hindi** (`hi`)

> iPhone “^FILENAME” को रीस्टोर नहीं किया जा सका क्योंकि बैकअप से कुछ फ़ाइलें रीस्टोर नहीं की जा सकीं।


## An error occurred

The generic variant. Says nothing about the cause.

**English** (`en`)

> Could not restore the iPhone “^FILENAME” because an error occurred.

**German** (`de`)

> Das iPhone „^FILENAME“ konnte wegen eines Fehlers nicht wiederhergestellt werden.

**French** (`fr`)

> Impossible de restaurer l’iPhone « ^FILENAME » car une erreur s’est produite.

**Spanish** (`es`)

> No se ha podido restaurar el iPhone “^FILENAME” porque se produjo un error.

**Italian** (`it`)

> Impossibile ripristinare l’iPhone “^FILENAME” perché si è verificato un errore.

**Dutch** (`nl`)

> De iPhone '^FILENAME' kon niet worden hersteld, omdat er zich een fout heeft voorgedaan.

**Portuguese (Brazil)** (`pt`)

> Não foi possível restaurar o iPhone “^FILENAME” porque ocorreu um erro.

**Portuguese (Portugal)** (`pt_PT`)

> Não foi possível restaurar o iPhone “^FILENAME” porque ocorreu um erro.

**Polish** (`pl`)

> Nie można odtworzyć iPhone’a „^FILENAME”, ponieważ wystąpił błąd.

**Turkish** (`tr`)

> Bir hata oluştuğu için “^FILENAME” adlı iPhone geri yüklenemedi.

**Russian** (`ru`)

> Не удалось восстановить iPhone «^FILENAME», так как произошла ошибка.

**Ukrainian** (`uk`)

> Не вдалося відновити iPhone «^FILENAME», оскільки сталася помилка.

**Swedish** (`sv`)

> Kunde inte återställa iPhone-enheten ”^FILENAME” eftersom ett fel inträffade.

**Danish** (`da`)

> Kunne ikke gendanne iPhone “^FILENAME”, fordi der opstod en fejl.

**Finnish** (`fi`)

> iPhonea ”^FILENAME” ei voida palauttaa, koska tapahtui virhe.

**Czech** (`cs`)

> iPhone „^FILENAME“ nelze obnovit, protože se vyskytla chyba.

**Slovak** (`sk`)

> Nepodarilo sa zálohovať iPhone „^FILENAME“, pretože sa vyskytla chyba.

**Hungarian** (`hu`)

> Nem sikerült visszaállítani a(z) „^FILENAME” iPhone-t, mert hiba történt.

**Romanian** (`ro`)

> iPhone‑ul „^FILENAME” nu a putut fi restaurat, deoarece a survenit o eroare.

**Croatian** (`hr`)

> Nije moguće obnoviti iPhone “^FILENAME” jer je došlo do greške.

**Greek** (`el`)

> Δεν ήταν δυνατή η επαναφορά του iPhone «^FILENAME», διότι παρουσιάστηκε σφάλμα.

**Japanese** (`ja`)

> エラーが発生したため、iPhone “^FILENAME”を復元できませんでした。

**Korean** (`ko`)

> 오류가 발생했기 때문에 ‘^FILENAME’ iPhone을 복원할 수 없습니다.

**Chinese (Simplified)** (`zh_CN`)

> 未能恢复iPhone“^FILENAME”，因为发生了一个错误。

**Chinese (Traditional)** (`zh_TW`)

> 無法回復iPhone「^FILENAME」，因為發生錯誤。

**Arabic** (`ar`)

> تعذرت استعادة الـ iPhone ‏"^FILENAME" بسبب حدوث خطأ.

**Hebrew** (`he`)

> לא היתה אפשרות לשחזר את ה-iPhone ‏״^FILENAME״ מאחר שאירעה שגיאה.

**Thai** (`th`)

> ไม่สามารถกู้คืน iPhone “^FILENAME” ได้เพราะเกิดข้อผิดพลาดขึ้น

**Vietnamese** (`vi`)

> Không thể khôi phục iPhone “^FILENAME” vì đã xảy ra lỗi.

**Indonesian** (`id`)

> Tidak dapat memulihkan iPhone “^FILENAME” karena terjadi kesalahan.

**Malay** (`ms`)

> Tidak dapat memulihkan iPhone “^FILENAME” kerana ralat telah berlaku.

**Hindi** (`hi`)

> iPhone “^FILENAME” को रीस्टोर नहीं किया जा सका क्योंकि कोई एरर हुआ।


## Could not be restored

The shortest variant, sometimes followed by a code in place of `^0`.

**English** (`en`)

> The iPhone “^FILENAME” could not be restored. ^0

**German** (`de`)

> Das iPhone „^FILENAME“ konnte nicht wiederhergestellt werden. ^0

**French** (`fr`)

> L’iPhone « ^FILENAME » n’a pas pu être restauré. ^0

**Spanish** (`es`)

> El iPhone “^FILENAME” no ha podido restaurarse. ^0

**Italian** (`it`)

> Impossibile ripristinare iPhone “^FILENAME”. ^0

**Dutch** (`nl`)

> De iPhone '^FILENAME' kon niet worden hersteld. ^0

**Portuguese (Brazil)** (`pt`)

> O iPhone “^FILENAME” não pôde ser restaurado. ^0

**Portuguese (Portugal)** (`pt_PT`)

> Não foi possível restaurar o iPhone “^FILENAME”. ^0

**Polish** (`pl`)

> Nie można odtworzyć iPhone'a „^FILENAME”. ^0

**Turkish** (`tr`)

> “^FILENAME” adlı iPhone’a geri yüklenemedi. ^0

**Russian** (`ru`)

> Не удалось восстановить iPhone «^FILENAME». ^0

**Ukrainian** (`uk`)

> Не вдається відновити iPhone «^FILENAME». ^0

**Swedish** (`sv`)

> iPhone-enheten ”^FILENAME” kunde inte återställas. ^0

**Danish** (`da`)

> iPhone “^FILENAME” kunne ikke gendannes. ^0

**Finnish** (`fi`)

> iPhonea ”^FILENAME” ei voitu palauttaa. ^0

**Czech** (`cs`)

> iPhone „^FILENAME“ nelze obnovit. ^0

**Slovak** (`sk`)

> iPhone „^FILENAME“ sa nepodarilo obnoviť. ^0

**Hungarian** (`hu`)

> A(z) „^FILENAME” iPhone nem állítható vissza. ^0

**Romanian** (`ro`)

> iPhone‑ul „^FILENAME” nu a putut fi restaurat. ^0

**Croatian** (`hr`)

> iPhone “^FILENAME” ne može se obnoviti. ^0

**Greek** (`el`)

> Δεν ήταν δυνατή η επαναφορά του iPhone «^FILENAME». ^0

**Japanese** (`ja`)

> iPhone “^FILENAME”を復元できませんでした。^0

**Korean** (`ko`)

> ‘^FILENAME’ iPhone을 복원할 수 없습니다. ^0

**Chinese (Simplified)** (`zh_CN`)

> 未能恢复iPhone“^FILENAME”。^0

**Chinese (Traditional)** (`zh_TW`)

> 無法回復iPhone「^FILENAME」。^0

**Arabic** (`ar`)

> تعذرت استعادة iPhone ‏"^FILENAME. ^0

**Hebrew** (`he`)

> לא ניתן היה לשחזר את ה-iPhone ״^FILENAME״. ^0

**Thai** (`th`)

> ไม่สามารถกู้คืน iPhone “^FILENAME” ได้ ^0

**Vietnamese** (`vi`)

> Không thể khôi phục iPhone “^FILENAME”. ^0

**Indonesian** (`id`)

> iPhone “^FILENAME” tidak dapat dipulihkan. ^0

**Malay** (`ms`)

> iPhone “^FILENAME” tidak dapat dipulihkan. ^0

**Hindi** (`hi`)

> iPhone “^FILENAME” को रीस्टोर नहीं किया जा सका। ^0


## An unknown error occurred (with number)

Carries an error number. If yours reads 2, that matches this bug.

**English** (`en`)

> Could not restore the iPhone “^FILENAME” because an unknown error occurred (^ERRORNUMBER).

**German** (`de`)

> Das iPhone „^FILENAME“ konnte wegen eines unbekannten Fehlers nicht wiederhergestellt werden (^ERRORNUMBER).

**French** (`fr`)

> Impossible de restaurer l’iPhone « ^FILENAME » car une erreur inconnue est survenue (^ERRORNUMBER).

**Spanish** (`es`)

> No se ha podido restaurar el iPhone “^FILENAME” porque se produjo un error desconocido (^ERRORNUMBER).

**Italian** (`it`)

> Impossibile ripristinare l’iPhone “^FILENAME” perché si è verificato un errore sconosciuto (^ERRORNUMBER).

**Dutch** (`nl`)

> De iPhone '^FILENAME' kon niet worden hersteld, omdat er zich een onbekende fout heeft voorgedaan (^ERRORNUMBER).

**Portuguese (Brazil)** (`pt`)

> Não foi possível restaurar o iPhone “^FILENAME” porque ocorreu um erro desconhecido (^ERRORNUMBER).

**Portuguese (Portugal)** (`pt_PT`)

> Não foi possível restaurar o iPhone “^FILENAME” porque ocorreu um erro desconhecido (^ERRORNUMBER).

**Polish** (`pl`)

> Nie można odtworzyć iPhone’a „^FILENAME”, ponieważ wystąpił nieznany błąd (^ERRORNUMBER).

**Turkish** (`tr`)

> Bilinmeyen bir hata (^ERRORNUMBER) oluştuğu için “^FILENAME” adlı iPhone geri yüklenemedi.

**Russian** (`ru`)

> Не удалось восстановить iPhone «^FILENAME» из-за возникновения неизвестной ошибки (^ERRORNUMBER).

**Ukrainian** (`uk`)

> Не вдалося відновити iPhone «^FILENAME», оскільки сталася невідома помилка (^ERRORNUMBER).

**Swedish** (`sv`)

> Kunde inte återställa iPhone-enheten ”^FILENAME” eftersom ett okänt fel inträffade (^ERRORNUMBER).

**Danish** (`da`)

> Kunne ikke gendanne iPhone “^FILENAME”, fordi der opstod en ukendt fejl (^ERRORNUMBER).

**Finnish** (`fi`)

> iPhonea ”^FILENAME” ei voida palauttaa, koska tapahtui tuntematon virhe (^ERRORNUMBER).

**Czech** (`cs`)

> iPhone „^FILENAME“ nelze obnovit, protože se vyskytla neznámá chyba (^ERRORNUMBER).

**Slovak** (`sk`)

> Nepodarilo sa obnoviť iPhone „^FILENAME“, pretože sa vyskytla neznáma chyba (^ERRORNUMBER).

**Hungarian** (`hu`)

> Nem sikerült visszaállítani a(z) „^FILENAME” iPhone-t, mert ismeretlen hiba történt (^ERRORNUMBER).

**Romanian** (`ro`)

> iPhone‑ul „^FILENAME” nu a putut fi restaurat, deoarece a survenit o eroare necunoscută (^ERRORNUMBER).

**Croatian** (`hr`)

> Nije moguće obnoviti iPhone “^FILENAME” jer je došlo do nepoznate greške (^ERRORNUMBER).

**Greek** (`el`)

> Δεν ήταν δυνατή η επαναφορά του iPhone «^FILENAME», διότι παρουσιάστηκε άγνωστο σφάλμα (^ERRORNUMBER).

**Japanese** (`ja`)

> 不明なエラー（^ERRORNUMBER）が発生したため、iPhone “^FILENAME”を復元できませんでした。

**Korean** (`ko`)

> 알 수 없는 오류(^ERRORNUMBER)가 발생했기 때문에 ‘^FILENAME’ iPhone을 복원할 수 없습니다.

**Chinese (Simplified)** (`zh_CN`)

> 未能恢复iPhone“^FILENAME”，因为发生了未知错误(^ERRORNUMBER)。

**Chinese (Traditional)** (`zh_TW`)

> 無法回復iPhone「^FILENAME」，因為發生未知錯誤（^ERRORNUMBER）。

**Arabic** (`ar`)

> تعذرت استعادة الـ iPhone ‏"^FILENAME" بسبب حدوث خطأ غير معروف (^ERRORNUMBER).

**Hebrew** (`he`)

> לא היתה אפשרות לשחזר את ה-iPhone ‏״^FILENAME״ מאחר שאירעה שגיאה בלתי ידועה (^ERRORNUMBER).

**Thai** (`th`)

> ไม่สามารถกู้คืน iPhone “^FILENAME” ได้เพราะเกิดข้อผิดพลาดที่ไม่ทราบสาเหตุขึ้น (^ERRORNUMBER)

**Vietnamese** (`vi`)

> Không thể khôi phục iPhone “^FILENAME” vì đã xảy ra lỗi không xác định (^ERRORNUMBER).

**Indonesian** (`id`)

> Tidak dapat memulihkan iPhone “^FILENAME” karena terjadi kesalahan yang tidak diketahui (^ERRORNUMBER).

**Malay** (`ms`)

> Tidak dapat memulihkan iPhone “^FILENAME” kerana ralat tidak diketahui telah berlaku (^ERRORNUMBER).

**Hindi** (`hi`)

> iPhone “^FILENAME” को रीस्टोर नहीं किया जा सका क्योंकि कोई अज्ञात एरर हुआ (^ERRORNUMBER)।


## Language-independent error codes

These appear identically in every language and are the most precise thing to
search for:

```
ErrorCode 2: _restoreRegularFiles:size: rename error: No such file or directory (2)
MBErrorDomain/2
NSPOSIXErrorDomain/2
Restore Failed (Error Code 2).
```

In the macOS unified log:

```
_stopWithError: Error Domain=MBErrorDomain Code=200
Device detached: AMDevice {UDID = ...}
Error erasing device: -10
```

`MBErrorDomain Code=200` is the generic "restore failed" bucket and does not by
itself indicate this bug. `Device detached` is emitted *after* the failure — it
is the device rebooting, not the cause, and it is the single most misleading
line in the whole log.
