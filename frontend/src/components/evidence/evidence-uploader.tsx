import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FilePlus, FolderPlus, Upload } from 'lucide-react';
import {
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
  type InputHTMLAttributes,
} from 'react';

interface Props {
  caseId: string;
  onUpload: (files: File[]) => void;
}

type DirectoryInputAttributes = InputHTMLAttributes<HTMLInputElement> & {
  webkitdirectory: string;
  directory: string;
};

const directoryInputProps: DirectoryInputAttributes = {
  webkitdirectory: '',
  directory: '',
};

export function EvidenceUploader({ caseId, onUpload }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const uploadFiles = (files: FileList | null) => {
    if (files && files.length > 0) {
      onUpload(Array.from(files));
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    uploadFiles(event.target.files);
    event.target.value = '';
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    uploadFiles(event.dataTransfer.files);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>上传证据</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className={`rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
            isDragging ? 'border-primary bg-primary/5' : 'border-border'
          }`}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          aria-label={`上传证据到案件 ${caseId}`}
        >
          <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
          <p className="mt-2 text-sm text-muted-foreground">
            拖拽文件或文件夹到此处上传，支持批量解析
          </p>
          <div className="mt-4 flex justify-center gap-4">
            <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
              <FilePlus className="mr-2 h-4 w-4" />
              上传文件
            </Button>
            <Button onClick={() => folderInputRef.current?.click()}>
              <FolderPlus className="mr-2 h-4 w-4" />
              选择文件夹
            </Button>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            multiple
            onChange={handleFileChange}
          />
          <input
            type="file"
            ref={folderInputRef}
            className="hidden"
            multiple
            onChange={handleFileChange}
            {...directoryInputProps}
          />
        </div>
      </CardContent>
    </Card>
  );
}
