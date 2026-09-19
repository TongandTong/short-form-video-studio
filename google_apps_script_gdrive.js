/**
 * Google Apps Script for Automated Short-Form Video Studio
 * 
 * วิธีติดตั้ง (ง่ายมาก ทำครั้งเดียว 2 นาที ฟรี 100%):
 * 1. เปิด https://script.google.com แล้วกด "โครงการใหม่" (New Project)
 * 2. ก๊อปปี้โค้ดทั้งหมดนี้ไปวางทับโค้ดเดิม
 * 3. กด "ทำให้ใช้งานได้" (Deploy) -> "การทำให้ใช้งานได้ใหม่" (New Deployment)
 * 4. เลือกประเภทเป็น "เว็บแอป" (Web App)
 * 5. ตั้งค่า:
 *    - ดำเนินการในฐานะ: ตัวฉันเอง (Me)
 *    - ผู้ที่มีสิทธิ์เข้าถึง: ทุกคน (Anyone)
 * 6. ก๊อปปี้ "URL เว็บแอป" ที่ได้ มาวางในช่อง Webhook URL ในแท็บ 6 ของ Shorts Studio
 */

function doPost(e) {
  try {
    var data = e.parameter;
    var fileName = data.file_name || ("shorts_" + new Date().getTime() + ".mp4");
    var folderId = data.folder_id || "";
    
    // เลือกโฟลเดอร์ปลายทาง
    var folder;
    if (folderId && folderId.trim() !== "") {
      folder = DriveApp.getFolderById(folderId.trim());
    } else {
      // โฟลเดอร์เริ่มต้นชื่อ "Why It Works Videos"
      var folders = DriveApp.getFoldersByName("Why It Works Videos");
      if (folders.hasNext()) {
        folder = folders.next();
      } else {
        folder = DriveApp.createFolder("Why It Works Videos");
      }
    }
    
    // บันทึกไฟล์วิดีโอ
    var blob = e.postData.contents;
    if (e.files && e.files.video) {
      blob = e.files.video;
    }
    
    var file = folder.createFile(fileName, blob, "video/mp4");
    
    // บันทึกไฟล์แคปชั่นข้อความคู่กัน
    var captionContent = "หัวข้อ: " + (data.title || "") + "\n\n" +
                         "แคปชั่น:\n" + (data.caption || "") + "\n\n" +
                         "แฮชแท็ก: " + (data.hashtags || "") + "\n\n" +
                         "คอมเมนต์ปักหมุด Affiliate:\n" + (data.affiliate_comment || "");
    folder.createFile(fileName.replace(".mp4", "_caption.txt"), captionContent, "text/plain");
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      file_id: file.getId(),
      file_url: file.getUrl()
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput("Why It Works Google Drive Webhook is Active!").setMimeType(ContentService.MimeType.TEXT);
}
