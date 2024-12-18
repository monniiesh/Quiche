// Copyright (C) 2020, Cloudflare, Inc.
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are
// met:
//
//     * Redistributions of source code must retain the above copyright notice,
//       this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
// IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
// THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
// PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
// CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
// EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
// PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
// PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
// LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
// NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

use std::fs::File;
use std::io::Write;
use std::env;
use std::sync::{Arc, Mutex};
use quiche_apps::args::*;
use quiche_apps::client::*;

fn main() {
    env_logger::builder().format_timestamp_nanos().init();

    // Parse CLI parameters.
    let docopt = docopt::Docopt::new(CLIENT_USAGE).unwrap();
    let conn_args = CommonArgs::with_docopt(&docopt);
    let args = ClientArgs::with_docopt(&docopt);

    // parse output file name
    let mut file_name = "video.mp4".to_string();
    let mut args_iter = env::args();

    while let Some(arg) = args_iter.next() {
        if arg == "--index" {
            if let Some(value) = args_iter.next() {
                file_name = value;
            } else {
                eprintln!("Error: --index requires a file name.");
                std::process::exit(1);
            }
        }
    }

    // Open the file for writing
    let file = Arc::new(Mutex::new(
        File::create(file_name).expect("Failed to create file"),
    ));

    // Define the output_sink closure to write data to the file
    let file_sink = {
        let file = Arc::clone(&file); // Clone the Arc to share the file
        move |data: String| {
            let mut file = file.lock().unwrap(); // Lock the file for thread-safe access
            file.write_all(data.as_bytes())
                .expect("Failed to write data to file");
        }
    };

    // Use the new output_sink to download data
    match connect(args, conn_args, file_sink) {
        Err(ClientError::HandshakeFail) => std::process::exit(-1),
        Err(ClientError::HttpFail) => std::process::exit(-2),
        Err(ClientError::Other(e)) => panic!("{}", e),
        Ok(_) => {
            println!("Data successfully saved.");
        }
    }
}

