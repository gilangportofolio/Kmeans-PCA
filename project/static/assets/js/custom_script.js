$(document).ready(function(){

    function change (note){
        var postdata = $('form#formSiswa').serializeArray();
        $.ajax({
            method: 'POST',
            url:'http://localhost/KP_absensi/ajx/onChange',
            data:postdata,
            success:function(data){
                console.log(data); 
                if(note == true){
                    Swal.fire({
                        position: 'bottom-end',
                        icon: 'success',
                        title: data,
                        showConfirmButton: false,
                        timer: 1500
                      })
                } 
                
            }
        });
    }
    $("select#pertemuan").change(function(){
        var id=$(this).val();
        var mapel = $('#nama_mapel').val();
        var id_kelas = $('#id_kelas').val();
        var id_jadwal = $('#id_jadwal').val();
        var rowCount = $('#tbl_absen_siswa tr').length - 1;
        $('input[name=rowCount]').val(rowCount);
        $.post("http://localhost/KP_absensi/ajx",
        {
            pertemuan: id,
            mata_pelajaran:mapel,
            kelas:id_kelas
        },
        function(data){
            // console.log(data);
            const obj = JSON.parse(data);

            $('#tbl_absen_siswa tr').remove();
            $('input#TotaljumlahSiswa').val(obj.jumlah);
            if(obj.jumlah==0){
                $('#tbl_absen_siswa').html(`<center>TIDAK ADA DATA DITEMUKAN!<center></br><center>Coba Muat Ulang Halaman ini !</center>`);
            }else{
                $('#tbl_absen_siswa').html(obj.data);
            }
            // console.log(obj.data);

        });
    }); 

    
    $("#tbl_absen_siswa").on("change","tbody tr select.status", function(){
        
        change(true);
        
    });
    $("#tbl_absen_siswa").on("keyup","tbody tr input.keterangan", function(){
        change(false);
    });
    

});