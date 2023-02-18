using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using RohanSpeechApp.Interfaces;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace BlazorAudioRecorder
{
    public class SaveAudio: Controller
    {
        Microsoft.AspNetCore.Hosting.IWebHostEnvironment _hostingEnvironment;
        private IVolumesRepository _volumesRepository;

        public SaveAudio(Microsoft.AspNetCore.Hosting.IWebHostEnvironment hostingEnvironment, IVolumesRepository volumesRepository)
        {
            _hostingEnvironment = hostingEnvironment;
            _volumesRepository = volumesRepository;

        }

        [Route("api/[controller]/Save")]
        [HttpPost]
        public async Task<IActionResult> Save(IFormFile file)
        {
            try
            {
                if (file.ContentType != "audio/wav")
                {
                    return BadRequest("Wrong file type");
                }

                var uploads = Path.Combine(_hostingEnvironment.WebRootPath, "uploads");//uploads where you want to save data inside wwwroot
                var filePath = Path.Combine(uploads, _volumesRepository.NextFileName(file.FileName));

                using (var fileStream = new FileStream(filePath, FileMode.Create))
                {
                    await file.CopyToAsync(fileStream);
                }

                return Ok("File uploaded successfully");
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.ToString());

                return BadRequest(ex.ToString());

            }

        }
    }
}
