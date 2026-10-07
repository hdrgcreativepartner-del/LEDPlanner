use std::{path::PathBuf, sync::Mutex};
use tauri::webview::DownloadEvent;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let last_directory = Mutex::new(None::<PathBuf>);
            tauri::WebviewWindowBuilder::from_config(app.handle(), &app.config().app.windows[0])?
                .on_download(move |webview, event| {
                    match event {
                        DownloadEvent::Requested { destination, .. } => {
                            let name = destination.file_name()
                                .map(|n| n.to_string_lossy().into_owned())
                                .unwrap_or_else(|| "LEDPlanner-export".into());
                            let extension = destination.extension()
                                .map(|e| e.to_string_lossy().into_owned());
                            let mut dialog = rfd::FileDialog::new()
                                .set_parent(&webview.window())
                                .set_title("Simpan ekspor LED Planner")
                                .set_file_name(name);
                            if let Some(ext) = extension.as_deref() {
                                dialog = dialog.add_filter("File ekspor", &[ext]);
                            }
                            if let Ok(folder) = last_directory.lock() {
                                if let Some(path) = folder.as_ref() {
                                    dialog = dialog.set_directory(path);
                                }
                            }
                            match dialog.save_file() {
                                Some(path) => {
                                    if let Ok(mut folder) = last_directory.lock() {
                                        *folder = path.parent().map(|p| p.to_path_buf());
                                    }
                                    *destination = path;
                                    true
                                }
                                None => false,
                            }
                        }
                        DownloadEvent::Finished { success: false, .. } => {
                            rfd::MessageDialog::new()
                                .set_parent(&webview.window())
                                .set_title("Ekspor gagal")
                                .set_description("File belum berhasil disimpan. Periksa folder tujuan dan coba ekspor kembali.")
                                .set_level(rfd::MessageLevel::Error)
                                .show();
                            true
                        }
                        _ => true,
                    }
                })
                .build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running LED Planner");
}
